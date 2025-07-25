# Generated by Django 5.2.4 on 2025-07-15 19:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('menu', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Orders',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_number', models.CharField(max_length=50, unique=True)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('ready_to_serve', 'Ready to Serve'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('order_type', models.CharField(choices=[('pre-selection', 'Pre-Selection'), ('walk-in', 'Walk-In')], default='pre-selection', max_length=20)),
                ('dining_method', models.CharField(choices=[('dine-in', 'Dine-In'), ('take-out', 'Take-Out')], max_length=20)),
                ('amount_paid', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('change_given', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('table_number', models.CharField(blank=True, max_length=10, null=True)),
                ('processed_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='OrderItems',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('price_at_order', models.DecimalField(decimal_places=2, max_digits=10)),
                ('variation', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='menu.variations')),
            ],
        ),
    ]
