# -*- coding: utf-8 -*-
"""Modelos de datos (SQLAlchemy) - Sistema de inventario y ventas."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Tendero(db.Model):
    __tablename__ = 'tendero'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    tienda = db.Column(db.String(120), nullable=False)
    usuario = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), default='tendero')

    productos = db.relationship('Producto', backref='tendero', lazy=True)
    ventas = db.relationship('Venta', backref='tendero', lazy=True)


class Producto(db.Model):
    __tablename__ = 'producto'
    id = db.Column(db.Integer, primary_key=True)
    tendero_id = db.Column(db.Integer, db.ForeignKey('tendero.id'), nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    categoria = db.Column(db.String(80))
    precio_compra = db.Column(db.Float, default=0)
    precio_venta = db.Column(db.Float, default=0)
    stock_actual = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=0)
    fecha_vencimiento = db.Column(db.Date, nullable=True)
    activo = db.Column(db.Boolean, default=True)


class Venta(db.Model):
    __tablename__ = 'venta'
    id = db.Column(db.Integer, primary_key=True)
    tendero_id = db.Column(db.Integer, db.ForeignKey('tendero.id'), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    total = db.Column(db.Float, default=0)

    detalles = db.relationship('DetalleVenta', backref='venta', lazy=True, cascade='all, delete-orphan')


class DetalleVenta(db.Model):
    __tablename__ = 'detalle_venta'
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('venta.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    producto = db.relationship('Producto')
