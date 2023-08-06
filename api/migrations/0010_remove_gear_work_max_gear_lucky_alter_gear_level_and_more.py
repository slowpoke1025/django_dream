# Generated by Django 4.2.3 on 2023-08-05 10:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_remove_gear_color_remove_gear_lucky_exercise_type_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gear',
            name='work_max',
        ),
        migrations.AddField(
            model_name='gear',
            name='lucky',
            field=models.CharField(choices=[(0, 'regular'), (1, 'advanced'), (2, 'high-end'), (3, 'epic')], default=0, max_length=10),
        ),
        migrations.AlterField(
            model_name='gear',
            name='level',
            field=models.PositiveIntegerField(choices=[(0, 'basic'), (1, 'intermediate'), (2, 'advanced')]),
        ),
        migrations.AlterField(
            model_name='gear',
            name='type',
            field=models.CharField(choices=[('b1', 'B1/髮型'), ('b2', 'B2/髮型'), ('b3', 'B3/髮型'), ('g1', 'G1/髮型'), ('g2', 'G2/髮型'), ('g3', 'G3/髮型'), ('c1', 'C1/上衣'), ('c2', 'C2/上衣'), ('c3', 'C3/上衣'), ('c4', 'C4/上衣'), ('c5', 'C5/上衣'), ('c6', 'C6/上衣'), ('pb1', 'Pb1/下著'), ('pb2', 'Pb2/下著'), ('pb3', 'Pb3/下著'), ('pg1', 'Pg1/下著'), ('pg2', 'Pg2/下著'), ('pg3', 'Pg3/下著'), ('s1', 'S1/鞋子'), ('s2', 'S2/鞋子'), ('s3', 'S3/鞋子'), ('s4', 'S4/鞋子'), ('s5', 'S5/鞋子'), ('s6', 'S6/鞋子')], max_length=10),
        ),
    ]