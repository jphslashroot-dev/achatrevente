import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime

# Configuration de l'application Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'achat-revente-super-secret-key-1095'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.root_path, 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # Limite d'upload à 8 Mo

# Extensions autorisées pour les photos
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Initialisation de la base de données
db = SQLAlchemy(app)

class Seller(db.Model):
    __tablename__ = 'sellers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    purchase_price = db.Column(db.Float, nullable=False, default=0.0)
    sale_price = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='En vente')  # 'En vente', 'Vendu', 'Réservé'
    image_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sold_at = db.Column(db.DateTime, nullable=True)
    seller = db.Column(db.String(100), nullable=True)
    platform = db.Column(db.String(100), nullable=True)

    @property
    def profit(self):
        if self.sale_price is not None:
            return round(self.sale_price - self.purchase_price, 2)
        return 0.0

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Création des tables au démarrage
with app.app_context():
    db.create_all()
    
    # Migration SQLite robuste pour ajouter la colonne 'seller' si elle n'existe pas
    try:
        from sqlalchemy import text
        db.session.execute(text("ALTER TABLE items ADD COLUMN seller VARCHAR(100)"))
        db.session.commit()
    except Exception:
        db.session.rollback()

    # Migration SQLite robuste pour ajouter la colonne 'platform' si elle n'existe pas
    try:
        from sqlalchemy import text
        db.session.execute(text("ALTER TABLE items ADD COLUMN platform VARCHAR(100)"))
        db.session.commit()
    except Exception:
        db.session.rollback()

MONTH_NAMES = {
    '01': 'Janvier', '02': 'Février', '03': 'Mars', '04': 'Avril',
    '05': 'Mai', '06': 'Juin', '07': 'Juillet', '08': 'Août',
    '09': 'Septembre', '10': 'Octobre', '11': 'Novembre', '12': 'Décembre'
}

def format_month_label(month_str):
    if not month_str or '-' not in month_str:
        return month_str
    year, month = month_str.split('-')
    return f"{MONTH_NAMES.get(month, month)} {year}"

@app.route('/')
def index():
    # Paramètres de filtre et recherche
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('q', '').strip()
    sort_by = request.args.get('sort_by', 'date_desc')
    month_filter = request.args.get('month', 'all')

    # Construction de la requête de base
    query = Item.query

    # Application de la recherche textuelle
    if search_query:
        query = query.filter(
            (Item.name.ilike(f'%{search_query}%')) | 
            (Item.description.ilike(f'%{search_query}%'))
        )

    # Application du filtre de statut
    if status_filter != 'all':
        query = query.filter(Item.status == status_filter)

    # Application du filtre de mois (created_at ou sold_at dans le mois choisi)
    if month_filter != 'all':
        try:
            year, month = map(int, month_filter.split('-'))
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            query = query.filter(
                ((Item.created_at >= start_date) & (Item.created_at < end_date)) |
                ((Item.sold_at >= start_date) & (Item.sold_at < end_date))
            )
        except Exception:
            pass

    # Tri des éléments
    if sort_by == 'date_asc':
        query = query.order_by(Item.created_at.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Item.purchase_price.desc())
    elif sort_by == 'price_asc':
        query = query.order_by(Item.purchase_price.asc())
    elif sort_by == 'profit_desc':
        query = query.order_by((Item.sale_price - Item.purchase_price).desc())
    else:
        # Par défaut : Date décroissante (plus récent d'abord)
        query = query.order_by(Item.created_at.desc())

    items = query.all()

    # Liste brute pour les calculs de statistiques
    all_items_unsorted = Item.query.all()

    # Extraction de tous les mois uniques d'activité pour le sélecteur
    available_months_set = set()
    for item in all_items_unsorted:
        if item.created_at:
            available_months_set.add(item.created_at.strftime('%Y-%m'))
        if item.sold_at:
            available_months_set.add(item.sold_at.strftime('%Y-%m'))
    
    sorted_months = sorted(list(available_months_set), reverse=True)
    available_months = [(m, format_month_label(m)) for m in sorted_months]

    # Calcul des statistiques (filtrées si un mois est sélectionné, sinon globales)
    if month_filter != 'all':
        try:
            year, month = map(int, month_filter.split('-'))
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            # Objets actifs achetés ce mois-ci
            active_items_month = [i for i in all_items_unsorted if i.status != 'Vendu' and i.created_at and start_date <= i.created_at < end_date]
            capital_invested = sum(i.purchase_price for i in active_items_month)
            
            # Objets vendus ce mois-ci
            sold_items_month = [i for i in all_items_unsorted if i.status == 'Vendu' and i.sold_at and start_date <= i.sold_at < end_date]
            total_revenue = sum(i.sale_price for i in sold_items_month if i.sale_price)
            total_profit = sum(i.profit for i in sold_items_month)
            cost_of_sold = sum(i.purchase_price for i in sold_items_month)
            
            count_active = len(active_items_month)
            count_sold = len(sold_items_month)
        except Exception:
            capital_invested = 0.0
            total_revenue = 0.0
            total_profit = 0.0
            cost_of_sold = 0.0
            count_active = 0
            count_sold = 0
    else:
        capital_invested = sum(i.purchase_price for i in all_items_unsorted if i.status != 'Vendu')
        total_revenue = sum(i.sale_price for i in all_items_unsorted if i.status == 'Vendu' and i.sale_price)
        total_profit = sum(i.profit for i in all_items_unsorted if i.status == 'Vendu')
        cost_of_sold = sum(i.purchase_price for i in all_items_unsorted if i.status == 'Vendu')
        count_active = len([i for i in all_items_unsorted if i.status != 'Vendu'])
        count_sold = len([i for i in all_items_unsorted if i.status == 'Vendu'])
        
    margin_percentage = round((total_profit / cost_of_sold * 100), 1) if cost_of_sold > 0 else 0.0

    stats = {
        'capital_invested': round(capital_invested, 2),
        'total_revenue': round(total_revenue, 2),
        'total_profit': round(total_profit, 2),
        'margin_percentage': margin_percentage,
        'count_active': count_active,
        'count_sold': count_sold
    }

    # Calcul des statistiques mensuelles détaillées (historique)
    monthly_data = {}
    for item in all_items_unsorted:
        # Achat (basé sur created_at)
        if item.created_at:
            m_purch = item.created_at.strftime('%Y-%m')
            if m_purch not in monthly_data:
                monthly_data[m_purch] = {
                    'month_label': format_month_label(m_purch),
                    'purchases_count': 0,
                    'purchases_total': 0.0,
                    'sales_count': 0,
                    'sales_total': 0.0,
                    'profit_total': 0.0,
                    'cost_of_sold': 0.0
                }
            monthly_data[m_purch]['purchases_count'] += 1
            monthly_data[m_purch]['purchases_total'] += item.purchase_price

        # Vente (basée sur sold_at)
        if item.status == 'Vendu' and item.sold_at:
            m_sold = item.sold_at.strftime('%Y-%m')
            if m_sold not in monthly_data:
                monthly_data[m_sold] = {
                    'month_label': format_month_label(m_sold),
                    'purchases_count': 0,
                    'purchases_total': 0.0,
                    'sales_count': 0,
                    'sales_total': 0.0,
                    'profit_total': 0.0,
                    'cost_of_sold': 0.0
                }
            monthly_data[m_sold]['sales_count'] += 1
            monthly_data[m_sold]['sales_total'] += (item.sale_price or 0.0)
            monthly_data[m_sold]['profit_total'] += item.profit
            monthly_data[m_sold]['cost_of_sold'] += item.purchase_price

    # Calcul des taux de marge pour chaque mois d'activité
    for m in monthly_data:
        cost = monthly_data[m]['cost_of_sold']
        profit = monthly_data[m]['profit_total']
        monthly_data[m]['margin_percentage'] = round((profit / cost * 100), 1) if cost > 0 else 0.0

    # Liste triée du plus récent au plus ancien
    monthly_stats = [
        {
            'month_key': k,
            **v
        }
        for k, v in sorted(monthly_data.items(), reverse=True)
    ]

    # Calcul des statistiques par vendeur (mensuel et global)
    seller_monthly_data = {}
    global_seller_data = {}

    for item in all_items_unsorted:
        if item.status == 'Vendu' and item.sold_at:
            m_key = item.sold_at.strftime('%Y-%m')
            seller_name = item.seller.strip() if (item.seller and item.seller.strip()) else "Non spécifié"
            
            # Mensuel
            if m_key not in seller_monthly_data:
                seller_monthly_data[m_key] = {}
            if seller_name not in seller_monthly_data[m_key]:
                seller_monthly_data[m_key][seller_name] = {
                    'sales_count': 0,
                    'sales_total': 0.0,
                    'profit_total': 0.0
                }
            seller_monthly_data[m_key][seller_name]['sales_count'] += 1
            seller_monthly_data[m_key][seller_name]['sales_total'] += (item.sale_price or 0.0)
            seller_monthly_data[m_key][seller_name]['profit_total'] += item.profit
            
            # Global
            if seller_name not in global_seller_data:
                global_seller_data[seller_name] = {
                    'sales_count': 0,
                    'sales_total': 0.0,
                    'profit_total': 0.0
                }
            global_seller_data[seller_name]['sales_count'] += 1
            global_seller_data[seller_name]['sales_total'] += (item.sale_price or 0.0)
            global_seller_data[seller_name]['profit_total'] += item.profit

    # Calcul des parts de ventes mensuelles (pourcentages)
    seller_monthly_stats = []
    for m_key, sellers in seller_monthly_data.items():
        total_m_sales = sum(s['sales_total'] for s in sellers.values())
        month_sellers = []
        for s_name, s_vals in sellers.items():
            share = round((s_vals['sales_total'] / total_m_sales * 100), 1) if total_m_sales > 0 else 0.0
            month_sellers.append({
                'name': s_name,
                'share_percentage': share,
                **s_vals
            })
        month_sellers = sorted(month_sellers, key=lambda x: x['sales_total'], reverse=True)
        seller_monthly_stats.append({
            'month_key': m_key,
            'month_label': format_month_label(m_key),
            'sellers': month_sellers
        })
    seller_monthly_stats = sorted(seller_monthly_stats, key=lambda x: x['month_key'], reverse=True)

    # Calcul des parts de ventes globales (pourcentages)
    total_g_sales = sum(s['sales_total'] for s in global_seller_data.values())
    seller_global_stats = []
    for s_name, s_vals in global_seller_data.items():
        share = round((s_vals['sales_total'] / total_g_sales * 100), 1) if total_g_sales > 0 else 0.0
        seller_global_stats.append({
            'name': s_name,
            'share_percentage': share,
            **s_vals
        })
    seller_global_stats = sorted(seller_global_stats, key=lambda x: x['sales_total'], reverse=True)

    # Récupérer la liste de tous les vendeurs déclarés
    sellers_list = Seller.query.order_by(Seller.name.asc()).all()

    return render_template(
        'index.html', 
        items=items, 
        stats=stats, 
        status_filter=status_filter, 
        search_query=search_query, 
        sort_by=sort_by,
        month_filter=month_filter,
        available_months=available_months,
        monthly_stats=monthly_stats,
        seller_monthly_stats=seller_monthly_stats,
        seller_global_stats=seller_global_stats,
        sellers=sellers_list
    )

@app.route('/add', methods=['POST'])
def add_item():
    try:
        name = request.form.get('name')
        description = request.form.get('description', '')
        purchase_price_raw = request.form.get('purchase_price', '0')
        sale_price_raw = request.form.get('sale_price', '')
        status = request.form.get('status', 'En vente')
        seller = request.form.get('seller', '').strip()
        platform = request.form.get('platform', '').strip()

        # Nettoyage et validation des prix
        purchase_price = float(purchase_price_raw) if purchase_price_raw else 0.0
        sale_price = float(sale_price_raw) if sale_price_raw else None

        if not name:
            flash("Le nom de l'objet est requis !", "error")
            return redirect(url_for('index'))

        # Gestion de l'image (caméra ou upload classique)
        image_filename = None
        image_base64 = request.form.get('image_base64')
        
        if image_base64 and ',' in image_base64:
            try:
                import base64
                header, encoded = image_base64.split(",", 1)
                data = base64.b64decode(encoded)
                
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
                filename = f"{timestamp}_capture.jpg"
                with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), "wb") as f:
                    f.write(data)
                image_filename = filename
            except Exception:
                pass
        
        # Si pas de capture caméra, on prend l'upload de fichier classique
        if not image_filename and 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                ext = file.filename.rsplit('.', 1)[1].lower()
                clean_name = secure_filename(file.filename.rsplit('.', 1)[0])
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
                filename = f"{timestamp}_{clean_name}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_filename = filename

        # Déterminer la date d'achat personnalisée
        purchase_date_raw = request.form.get('purchase_date')
        created_at = datetime.utcnow()
        if purchase_date_raw:
            try:
                now_time = datetime.utcnow().time()
                parsed_date = datetime.strptime(purchase_date_raw, '%Y-%m-%d')
                created_at = datetime.combine(parsed_date.date(), now_time)
            except Exception:
                pass

        # Déterminer la date de vente personnalisée ou automatique
        sold_at = None
        if status == 'Vendu':
            sold_date_raw = request.form.get('sold_date')
            if sold_date_raw:
                try:
                    now_time = datetime.utcnow().time()
                    parsed_date = datetime.strptime(sold_date_raw, '%Y-%m-%d')
                    sold_at = datetime.combine(parsed_date.date(), now_time)
                except Exception:
                    sold_at = datetime.utcnow()
            else:
                sold_at = datetime.utcnow()

        new_item = Item(
            name=name,
            description=description,
            purchase_price=purchase_price,
            sale_price=sale_price,
            status=status,
            image_filename=image_filename,
            created_at=created_at,
            sold_at=sold_at,
            seller=seller,
            platform=platform
        )

        db.session.add(new_item)
        db.session.commit()
        flash("L'objet a été ajouté avec succès !", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Une erreur est survenue lors de l'ajout : {str(e)}", "error")

    return redirect(url_for('index'))

@app.route('/edit/<int:item_id>', methods=['POST'])
def edit_item(item_id):
    try:
        item = Item.query.get_or_404(item_id)
        
        name = request.form.get('name')
        description = request.form.get('description', '')
        purchase_price_raw = request.form.get('purchase_price', '0')
        sale_price_raw = request.form.get('sale_price', '')
        status = request.form.get('status', 'En vente')
        seller = request.form.get('seller', '').strip()
        platform = request.form.get('platform', '').strip()

        if not name:
            flash("Le nom de l'objet est requis !", "error")
            return redirect(url_for('index'))

        # Mises à jour des champs de base
        item.name = name
        item.description = description
        item.purchase_price = float(purchase_price_raw) if purchase_price_raw else 0.0
        item.seller = seller
        item.platform = platform
        
        # Gestion du prix de vente
        old_status = item.status
        item.status = status
        
        if sale_price_raw:
            item.sale_price = float(sale_price_raw)
        else:
            item.sale_price = None

        # Saisie personnalisée de la date d'achat
        purchase_date_raw = request.form.get('purchase_date')
        if purchase_date_raw:
            try:
                orig_time = item.created_at.time() if item.created_at else datetime.utcnow().time()
                parsed_date = datetime.strptime(purchase_date_raw, '%Y-%m-%d')
                item.created_at = datetime.combine(parsed_date.date(), orig_time)
            except Exception:
                pass

        # Gestion de la date de revente
        if status == 'Vendu':
            sold_date_raw = request.form.get('sold_date')
            if sold_date_raw:
                try:
                    orig_time = item.sold_at.time() if item.sold_at else datetime.utcnow().time()
                    parsed_date = datetime.strptime(sold_date_raw, '%Y-%m-%d')
                    item.sold_at = datetime.combine(parsed_date.date(), orig_time)
                except Exception:
                    if item.sold_at is None:
                        item.sold_at = datetime.utcnow()
            else:
                if old_status != 'Vendu' or item.sold_at is None:
                    item.sold_at = datetime.utcnow()
        else:
            item.sold_at = None

        # Gestion de l'image (caméra ou upload classique)
        image_filename = None
        image_base64 = request.form.get('image_base64')
        
        if image_base64 and ',' in image_base64:
            try:
                import base64
                header, encoded = image_base64.split(",", 1)
                data = base64.b64decode(encoded)
                
                # Supprimer l'ancienne image si elle existe
                if item.image_filename:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], item.image_filename)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except OSError:
                            pass
                
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
                filename = f"{timestamp}_capture.jpg"
                with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), "wb") as f:
                    f.write(data)
                item.image_filename = filename
                image_filename = filename
            except Exception:
                pass
        
        if not image_filename and 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                # Supprimer l'ancienne image si elle existe
                if item.image_filename:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], item.image_filename)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except OSError:
                            pass
                
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                ext = file.filename.rsplit('.', 1)[1].lower()
                clean_name = secure_filename(file.filename.rsplit('.', 1)[0])
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
                filename = f"{timestamp}_{clean_name}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                item.image_filename = filename

        db.session.commit()
        flash("L'objet a été mis à jour avec succès !", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Une erreur est survenue lors de la mise à jour : {str(e)}", "error")

    return redirect(url_for('index'))

@app.route('/quick_sell/<int:item_id>', methods=['POST'])
def quick_sell(item_id):
    try:
        item = Item.query.get_or_404(item_id)
        sale_price_raw = request.form.get('sale_price')
        if not sale_price_raw:
            flash("Le prix de revente est requis pour valider la vente !", "error")
            return redirect(url_for('index'))

        item.status = 'Vendu'
        item.sale_price = float(sale_price_raw)
        item.sold_at = datetime.utcnow()

        db.session.commit()
        flash(f"L'objet '{item.name}' a été marqué comme vendu !", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Une erreur est survenue lors de la vente rapide : {str(e)}", "error")
    return redirect(url_for('index'))

@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    try:
        item = Item.query.get_or_404(item_id)
        
        # Supprimer le fichier image associé
        if item.image_filename:
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], item.image_filename)
            if os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except OSError:
                    pass

        db.session.delete(item)
        db.session.commit()
        flash("L'objet a été supprimé !", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Une erreur est survenue lors de la suppression : {str(e)}", "error")

    return redirect(url_for('index'))

@app.route('/add_seller', methods=['POST'])
def add_seller():
    try:
        name = request.form.get('name', '').strip()
        if not name:
            flash("Le nom du vendeur est requis !", "error")
            return redirect(url_for('index'))
        
        # Vérifier si déjà existant
        existing = Seller.query.filter_by(name=name).first()
        if existing:
            flash("Ce vendeur existe déjà !", "error")
            return redirect(url_for('index'))

        new_seller = Seller(name=name)
        db.session.add(new_seller)
        db.session.commit()
        flash(f"Vendeur '{name}' déclaré avec succès !", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de l'ajout du vendeur : {str(e)}", "error")
    return redirect(url_for('index'))

@app.route('/delete_seller/<int:seller_id>', methods=['POST'])
def delete_seller(seller_id):
    try:
        seller = Seller.query.get_or_404(seller_id)
        db.session.delete(seller)
        db.session.commit()
        flash(f"Vendeur '{seller.name}' supprimé !", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression du vendeur : {str(e)}", "error")
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Écoute sur le port 9096 comme demandé
    app.run(host='0.0.0.0', port=9096, debug=True)
