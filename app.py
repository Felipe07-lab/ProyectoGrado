# -*- coding: utf-8 -*-
"""
Sistema web para la gestión de inventario y ventas en tiendas de barrio
Proyecto de Grado - UNAD - Ingeniería de Sistemas
Prototipo funcional (TRL5) - Fase 4

Autores: Andrés Felipe Velandia Naranjo, Andrés Felipe Pérez Pérez
"""
import os
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

from models import db, Tendero, Producto, Venta, DetalleVenta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave-secreta-dev-cambiar-en-produccion')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'tienda.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

DIAS_ALERTA_VENCIMIENTO = 7


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'tendero_id' not in session:
            flash('Debe iniciar sesión para continuar.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


def get_alertas(tendero_id):
    hoy = datetime.utcnow().date()
    limite = hoy + timedelta(days=DIAS_ALERTA_VENCIMIENTO)
    productos = Producto.query.filter_by(tendero_id=tendero_id, activo=True).all()
    alertas_stock = [p for p in productos if p.stock_actual <= p.stock_minimo]
    alertas_vencimiento = [
        p for p in productos
        if p.fecha_vencimiento is not None and p.fecha_vencimiento <= limite
    ]
    return alertas_stock, alertas_vencimiento


# ---------------------------------------------------------------- AUTH
@app.route('/', methods=['GET'])
def index():
    if 'tendero_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario', '').strip()
        password = request.form.get('password', '')
        tendero = Tendero.query.filter_by(usuario=usuario).first()
        if tendero and check_password_hash(tendero.password_hash, password):
            session['tendero_id'] = tendero.id
            session['tendero_nombre'] = tendero.nombre
            session['tienda'] = tendero.tienda
            flash(f'Bienvenido(a), {tendero.nombre}.', 'success')
            return redirect(url_for('dashboard'))
        flash('Usuario o contraseña incorrectos.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('login'))


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        tienda = request.form.get('tienda', '').strip()
        usuario = request.form.get('usuario', '').strip()
        password = request.form.get('password', '')
        if not all([nombre, tienda, usuario, password]):
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('registro.html')
        if Tendero.query.filter_by(usuario=usuario).first():
            flash('Ese nombre de usuario ya está registrado.', 'danger')
            return render_template('registro.html')
        t = Tendero(
            nombre=nombre, tienda=tienda, usuario=usuario,
            password_hash=generate_password_hash(password), rol='tendero'
        )
        db.session.add(t)
        db.session.commit()
        flash('Registro exitoso. Ahora puede iniciar sesión.', 'success')
        return redirect(url_for('login'))
    return render_template('registro.html')


# ---------------------------------------------------------------- DASHBOARD
@app.route('/dashboard')
@login_required
def dashboard():
    tid = session['tendero_id']
    alertas_stock, alertas_venc = get_alertas(tid)

    hoy = datetime.utcnow().date()
    ventas_hoy = Venta.query.filter(
        Venta.tendero_id == tid,
        func.date(Venta.fecha) == hoy
    ).all()
    total_hoy = sum(v.total for v in ventas_hoy)
    num_transacciones = len(ventas_hoy)

    top_productos = (
        db.session.query(Producto.nombre, func.sum(DetalleVenta.cantidad).label('vendidos'))
        .join(DetalleVenta, DetalleVenta.producto_id == Producto.id)
        .join(Venta, Venta.id == DetalleVenta.venta_id)
        .filter(Venta.tendero_id == tid)
        .group_by(Producto.id)
        .order_by(func.sum(DetalleVenta.cantidad).desc())
        .limit(5)
        .all()
    )

    return render_template(
        'dashboard.html',
        alertas_stock=alertas_stock,
        alertas_venc=alertas_venc,
        total_hoy=total_hoy,
        num_transacciones=num_transacciones,
        top_productos=top_productos,
    )


# ---------------------------------------------------------------- PRODUCTOS (INVENTARIO)
@app.route('/productos')
@login_required
def productos():
    tid = session['tendero_id']
    lista = Producto.query.filter_by(tendero_id=tid, activo=True).order_by(Producto.nombre).all()
    return render_template('productos.html', productos=lista)


@app.route('/productos/nuevo', methods=['GET', 'POST'])
@login_required
def producto_nuevo():
    if request.method == 'POST':
        try:
            p = Producto(
                tendero_id=session['tendero_id'],
                nombre=request.form['nombre'].strip(),
                categoria=request.form.get('categoria', '').strip(),
                precio_compra=float(request.form.get('precio_compra') or 0),
                precio_venta=float(request.form.get('precio_venta') or 0),
                stock_actual=int(request.form.get('stock_actual') or 0),
                stock_minimo=int(request.form.get('stock_minimo') or 0),
                fecha_vencimiento=_parse_date(request.form.get('fecha_vencimiento')),
                activo=True,
            )
            db.session.add(p)
            db.session.commit()
            flash(f'Producto "{p.nombre}" registrado correctamente.', 'success')
            return redirect(url_for('productos'))
        except ValueError:
            flash('Verifique que los valores numéricos sean correctos.', 'danger')
    return render_template('producto_form.html', producto=None)


@app.route('/productos/<int:pid>/editar', methods=['GET', 'POST'])
@login_required
def producto_editar(pid):
    p = Producto.query.filter_by(id=pid, tendero_id=session['tendero_id']).first_or_404()
    if request.method == 'POST':
        p.nombre = request.form['nombre'].strip()
        p.categoria = request.form.get('categoria', '').strip()
        p.precio_compra = float(request.form.get('precio_compra') or 0)
        p.precio_venta = float(request.form.get('precio_venta') or 0)
        p.stock_actual = int(request.form.get('stock_actual') or 0)
        p.stock_minimo = int(request.form.get('stock_minimo') or 0)
        p.fecha_vencimiento = _parse_date(request.form.get('fecha_vencimiento'))
        db.session.commit()
        flash('Producto actualizado correctamente.', 'success')
        return redirect(url_for('productos'))
    return render_template('producto_form.html', producto=p)


@app.route('/productos/<int:pid>/desactivar', methods=['POST'])
@login_required
def producto_desactivar(pid):
    p = Producto.query.filter_by(id=pid, tendero_id=session['tendero_id']).first_or_404()
    p.activo = False
    db.session.commit()
    flash(f'Producto "{p.nombre}" desactivado.', 'info')
    return redirect(url_for('productos'))


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


# ---------------------------------------------------------------- VENTAS
@app.route('/ventas/nueva', methods=['GET', 'POST'])
@login_required
def venta_nueva():
    tid = session['tendero_id']
    if request.method == 'POST':
        producto_ids = request.form.getlist('producto_id')
        cantidades = request.form.getlist('cantidad')
        if not producto_ids:
            flash('Debe agregar al menos un producto a la venta.', 'danger')
            return redirect(url_for('venta_nueva'))

        venta = Venta(tendero_id=tid, fecha=datetime.utcnow(), total=0)
        db.session.add(venta)
        db.session.flush()

        total = 0.0
        for pid_str, cant_str in zip(producto_ids, cantidades):
            try:
                pid = int(pid_str)
                cant = int(cant_str)
            except ValueError:
                continue
            if cant <= 0:
                continue
            producto = Producto.query.filter_by(id=pid, tendero_id=tid).first()
            if not producto:
                continue
            cant = min(cant, producto.stock_actual)
            if cant <= 0:
                continue
            subtotal = cant * producto.precio_venta
            detalle = DetalleVenta(
                venta_id=venta.id, producto_id=producto.id,
                cantidad=cant, subtotal=subtotal
            )
            producto.stock_actual -= cant
            total += subtotal
            db.session.add(detalle)

        venta.total = total
        db.session.commit()
        flash(f'Venta registrada por un total de ${total:,.0f}.', 'success')
        return redirect(url_for('dashboard'))

    lista = Producto.query.filter_by(tendero_id=tid, activo=True).filter(Producto.stock_actual > 0).order_by(Producto.nombre).all()
    return render_template('venta_form.html', productos=lista)


@app.route('/ventas')
@login_required
def ventas_lista():
    tid = session['tendero_id']
    lista = Venta.query.filter_by(tendero_id=tid).order_by(Venta.fecha.desc()).limit(50).all()
    return render_template('ventas.html', ventas=lista)


# ---------------------------------------------------------------- REPORTES
@app.route('/reportes')
@login_required
def reportes():
    tid = session['tendero_id']
    hoy = datetime.utcnow().date()
    hace_7 = hoy - timedelta(days=7)
    hace_30 = hoy - timedelta(days=30)

    def total_periodo(desde):
        q = Venta.query.filter(Venta.tendero_id == tid, func.date(Venta.fecha) >= desde)
        return sum(v.total for v in q.all()), q.count()

    total_dia, trans_dia = total_periodo(hoy)
    total_semana, trans_semana = total_periodo(hace_7)
    total_mes, trans_mes = total_periodo(hace_30)

    rotacion = (
        db.session.query(Producto.nombre, func.sum(DetalleVenta.cantidad).label('vendidos'))
        .join(DetalleVenta, DetalleVenta.producto_id == Producto.id)
        .join(Venta, Venta.id == DetalleVenta.venta_id)
        .filter(Venta.tendero_id == tid)
        .group_by(Producto.id)
        .order_by(func.sum(DetalleVenta.cantidad).desc())
        .all()
    )

    return render_template(
        'reportes.html',
        total_dia=total_dia, trans_dia=trans_dia,
        total_semana=total_semana, trans_semana=trans_semana,
        total_mes=total_mes, trans_mes=trans_mes,
        rotacion=rotacion,
    )


# ---------------------------------------------------------------- API (JSON) de apoyo
@app.route('/api/producto/<int:pid>')
@login_required
def api_producto(pid):
    p = Producto.query.filter_by(id=pid, tendero_id=session['tendero_id']).first_or_404()
    return jsonify({
        'id': p.id, 'nombre': p.nombre, 'precio_venta': p.precio_venta,
        'stock_actual': p.stock_actual
    })


def crear_datos_demo():
    """Crea un tendero y productos de ejemplo si la base está vacía (solo para demo/pruebas)."""
    if Tendero.query.first():
        return
    demo = Tendero(
        nombre='Tendero Demo', tienda='Tienda Don José',
        usuario='demo', password_hash=generate_password_hash('demo1234'), rol='tendero'
    )
    db.session.add(demo)
    db.session.commit()

    hoy = datetime.utcnow().date()
    productos_demo = [
        ('Arroz x 500g', 'Granos', 1800, 2300, 20, 5, hoy + timedelta(days=120)),
        ('Leche entera 1L', 'Lácteos', 3200, 3900, 10, 5, hoy + timedelta(days=3)),
        ('Gaseosa 1.5L', 'Bebidas', 3800, 5200, 15, 4, hoy + timedelta(days=200)),
        ('Pan tajado', 'Panadería', 4200, 5800, 2, 5, hoy + timedelta(days=6)),
        ('Aceite 1L', 'Abarrotes', 7500, 9800, 8, 3, hoy + timedelta(days=300)),
    ]
    for nombre, cat, pc, pv, stock, minimo, venc in productos_demo:
        db.session.add(Producto(
            tendero_id=demo.id, nombre=nombre, categoria=cat,
            precio_compra=pc, precio_venta=pv, stock_actual=stock,
            stock_minimo=minimo, fecha_vencimiento=venc, activo=True
        ))
    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)
        db.create_all()
        crear_datos_demo()
    app.run(debug=True, host='0.0.0.0', port=5000)
