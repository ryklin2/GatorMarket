# import necessary blueprints and libraries
from flask import Blueprint, jsonify, request, send_from_directory
from app import get_db_connection
from auth import token_required
import os
import uuid
import re
import magic  # for MIME type checking
import traceback

# create blueprint for all product related routes
products_bp = Blueprint('products', __name__, url_prefix='/products')

# defining constants for image handling
UPLOAD_FOLDER = '/app/product_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ALLOWED_MIMES = {'image/png', 'image/jpeg'}

# ensure image directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# checking if file has valid extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# preventing directory traversal or invalid characters 
def secure_filename(filename):
    filename = os.path.basename(filename)
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    return filename if filename else 'file'

# confirms MIME type of image is safe and matches declared extension
def verify_image_content(file):
    # Read the first 2048 bytes to determine file type
    file_head = file.read(2048)
    file.seek(0)  # Reset file pointer
    mime_type = magic.from_buffer(file_head, mime=True)
    return mime_type in ALLOWED_MIMES

# route for image uploads, stores images with a unique filename
@products_bp.route('/upload-image', methods=['POST'])
@token_required
def upload_image(current_user):
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed types: png, jpg, jpeg'}), 400
            
        if not verify_image_content(file):
            return jsonify({'error': 'Invalid image content or potentially unsafe file'}), 400
            
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        image_url = f'/products/serve-image/{unique_filename}'
        return jsonify({'url': image_url}), 200
    except Exception as e:
        print(f"Error uploading image: {e}")
        return jsonify({'error': f'Failed to upload image: {str(e)}'}), 500

# securely serves product images if approved
@products_bp.route('/serve-image/<path:filename>', methods=['GET'])
def serve_image(filename):
    clean_filename = os.path.basename(filename)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.product_id, p.approval_status 
        FROM products p
        JOIN product_images pi ON p.product_id = pi.product_id
        WHERE pi.image_url LIKE %s
    """, (f'%{clean_filename}',))
    product = cursor.fetchone()
    cursor.close()
    conn.close()

    if product and product['approval_status'] == 'approved':
        return send_from_directory(UPLOAD_FOLDER, clean_filename)
    elif product and product['approval_status'] == 'pending':
        return send_from_directory('/app/static/images', 'pending_approval.png')
    else:
        return jsonify({'error': 'Image not found'}), 404

# fetches full product details and related images
@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch product info
    cursor.execute("""
        SELECT p.*, u.username,
               (SELECT AVG(rating) FROM reviews WHERE seller_id = p.user_id) as seller_rating
        FROM products p
        JOIN users u ON p.user_id = u.user_id
        WHERE p.product_id = %s
    """, (product_id,))
    product = cursor.fetchone()

    if product:
        # Fetch images
        cursor.execute("SELECT image_url FROM product_images WHERE product_id = %s", (product_id,))
        images = cursor.fetchall()
        product['images'] = [img['image_url'] for img in images]

        product['seller_rating'] = float(product['seller_rating']) if product['seller_rating'] else 0.0

    cursor.close()
    conn.close()

    if product:
        return jsonify(product)
    else:
        return jsonify({'error': 'Product not found'}), 404

# enables product filtering by search term, category, or user
@products_bp.route('/search', methods=['GET'])
def search_products():
    term = request.args.get('term')
    category = request.args.get('category')
    user_id = request.args.get('user_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT p.*, u.username,
               (SELECT AVG(rating) FROM reviews WHERE seller_id = p.user_id) as seller_rating
        FROM products p
        JOIN users u ON p.user_id = u.user_id
        JOIN categories c ON p.category_id = c.category_id
        WHERE p.approval_status = 'approved'
    """
    params = []

    # filter out sold items if not viewing a specific user's listings
    if not user_id:
        query += "AND p.status = 'active'"
    
    if term:
        query += " AND (p.name LIKE %s OR p.description LIKE %s)"
        params.extend([f"%{term}%", f"%{term}%"])
    if category and category != "All Categories":
        query += " AND c.name = %s"
        params.append(category)
    if user_id:
        query += " AND p.user_id = %s"
        params.append(user_id)
    query += " ORDER BY p.created_at DESC"

    cursor.execute(query, tuple(params))
    products = cursor.fetchall()
    for product in products:
        cursor.execute("SELECT image_url FROM product_images WHERE product_id = %s", (product['product_id'],))
        images = cursor.fetchall()
        product['images'] = [img['image_url'] for img in images]

        product['seller_rating'] = float(product['seller_rating']) if product['seller_rating'] else 0.0
    cursor.close()
    conn.close()
    return jsonify(products)

# creates new product listing w/ image validation and saving
@products_bp.route('/', methods=['POST'])
@token_required
def create_product(current_user):
    try:
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Check user's total products first
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM products 
                WHERE user_id = %s AND status = 'active'
            """, (current_user['user_id'],))
            product_count = cursor.fetchone()[0]
            
            if product_count >= 100:
                cursor.close()
                conn.close()
                return jsonify({'error': 'You have reached the maximum limit of 100 active products'}), 400

            # Validate all images before creating the product
            images = request.files.getlist('images')
            
            # Check if any images were provided
            if not images or len(images) == 0:
                cursor.close()
                conn.close()
                return jsonify({'error': 'At least one image is required for the product'}), 400
                
            # Validate each image
            for file in images:
                if not file or file.filename == '':
                    cursor.close()
                    conn.close()
                    return jsonify({'error': 'Invalid file uploaded'}), 400
                    
                if not allowed_file(file.filename):
                    cursor.close()
                    conn.close()
                    return jsonify({'error': f'Invalid file type for {file.filename}. Allowed types: png, jpg, jpeg'}), 400
                
                if not verify_image_content(file):
                    cursor.close()
                    conn.close()
                    return jsonify({'error': f'Invalid image content or potentially unsafe file: {file.filename}'}), 400
            
            # If all images passed validation, continue with product creation
            name = request.form.get('name')
            description = request.form.get('description')
            price = request.form.get('price')
            condition = request.form.get('condition')
            category_id = request.form.get('category_id')

            # Insert product
            cursor.execute("""
                INSERT INTO products (
                    user_id, name, description, price, 
                    `condition`, category_id, approval_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                current_user['user_id'], name, description, price,
                condition, category_id, 'pending'
            ))
            product_id = cursor.lastrowid

            # Save images - we've already validated them above
            for file in images:
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                file.save(file_path)
                image_url = f'/products/serve-image/{unique_filename}'

                cursor.execute("""
                    INSERT INTO product_images (product_id, image_url)
                    VALUES (%s, %s)
                """, (product_id, image_url))

            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({'message': 'Product created successfully', 'product_id': product_id}), 201

        else:
            return jsonify({'error': 'Unsupported content type. Use multipart/form-data for file uploads.'}), 400
    except Exception as e:
        print(f"Error creating product: {e}")
        return jsonify({'error': f'Failed to create product: {str(e)}'}), 500


# route to update product details if user is owner
@products_bp.route('/<int:product_id>', methods=['PUT'])
@token_required
def update_product(current_user, product_id):
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_id FROM products WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        if not product or product['user_id'] != current_user['user_id']:
            return jsonify({'error': 'Unauthorized to update this product'}), 403

        query = """
            UPDATE products
            SET name = %s,
                description = %s,
                price = %s,
                `condition` = %s,
                category_id = %s
            WHERE product_id = %s
        """
        cursor.execute(query, (
            data.get('name'),
            data.get('description'),
            data.get('price'),
            data.get('condition'),
            data.get('category_id'),
            product_id
        ))
        conn.commit()

        # Get updated product details
        cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
        updated_product = cursor.fetchone()

        # Get associated images
        cursor.execute("SELECT image_url FROM product_images WHERE product_id = %s", (product_id,))
        images = cursor.fetchall()
        updated_product['images'] = [img['image_url'] for img in images]

        cursor.close()
        conn.close()

        return jsonify({'message': 'Product updated successfully', 'product': updated_product}), 200
    except Exception as e:
        print(f"Error updating product: {e}")
        return jsonify({'error': f'Failed to update product: {str(e)}'}), 500


# route to delete product and related records like messaging, wishlist, conversations, etc
@products_bp.route('/<int:product_id>', methods=['DELETE'])
@token_required
def delete_product(current_user, product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # do we have right user?
        cursor.execute("SELECT user_id FROM products WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        if not product or product[0] != current_user['user_id']:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Unauthorized to delete this product'}), 403
        
        
        # Step 1: Delete from wishlist_tracking
        cursor.execute("DELETE FROM wishlist_tracking WHERE product_id = %s", (product_id,))
        
        # Step 2: Find all conversations related to this product
        cursor.execute("SELECT conversation_id FROM conversations WHERE product_id = %s", (product_id,))
        conversations = cursor.fetchall()
        
        # Step 3: Delete messages from these conversations
        for conv in conversations:
            conversation_id = conv[0]
            cursor.execute("DELETE FROM messages WHERE conversation_id = %s", (conversation_id,))
            
        # Step 4: Delete conversation participants
        for conv in conversations:
            conversation_id = conv[0]
            cursor.execute("DELETE FROM conversation_participants WHERE conversation_id = %s", (conversation_id,))
            
        # Step 5: Delete conversations
        cursor.execute("DELETE FROM conversations WHERE product_id = %s", (product_id,))
        
        # Step 6: Delete product images (This should happen automatically due to ON DELETE CASCADE)
        
        # Step 7: Finally delete the product
        cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
        affected = cursor.rowcount
        
        # Commit transaction
        conn.commit()
        cursor.close()
        conn.close()
        
        if affected:
            return jsonify({'message': 'Product deleted successfully', 'product_id': product_id})
        else:
            return jsonify({'error': 'Product not found'}), 404
            
    except Exception as e:
        # Rollback in case of error
        try:
            conn.rollback()
        except:
            pass
            
        print(f"Error deleting product: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Failed to delete product: {str(e)}'}), 500

@products_bp.route('/<int:product_id>/mark-sold', methods=['PUT'])
@token_required
def mark_product_as_sold(current_user, product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM products WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        if not product or product[0] != current_user['user_id']:
            return jsonify({'error': 'Unauthorized'}), 403
        cursor.execute("UPDATE products SET status = 'sold' WHERE product_id = %s", (product_id,))
        cursor.execute("UPDATE wishlist_tracking SET notified = FALSE WHERE product_id = %s", (product_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Product marked as sold'}), 200
    except Exception as e:
        print(f"Error marking product as sold: {e}")
        return jsonify({'error': 'Failed to mark product as sold'}), 500
    
