# Generated by Django 5.2.3 on 2025-06-19 07:05

import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='JudgeExpertise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('presentation_link', models.URLField(blank=True)),
                ('members', models.TextField(help_text='Comma-separated list of team members')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Judge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unique_token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('has_submitted', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('expertise_areas', models.ManyToManyField(to='judging.judgeexpertise')),
            ],
        ),
        migrations.CreateModel(
            name='JudgingCriteria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('weight', models.DecimalField(decimal_places=2, max_digits=5)),
                ('expertise_areas', models.ManyToManyField(blank=True, to='judging.judgeexpertise')),
            ],
            options={
                'verbose_name_plural': 'Judging Criteria',
            },
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('comments', models.TextField(blank=True)),
                ('judge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='judging.judge')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='judging.team')),
            ],
            options={
                'unique_together': {('judge', 'team')},
            },
        ),
        migrations.CreateModel(
            name='TeamFinalScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantum_tech_score', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('social_impact_score', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('innovation_score', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('presentation_score', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('business_viability_score', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('final_weighted_score', models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ('rank', models.IntegerField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('team', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='judging.team')),
            ],
        ),
        migrations.CreateModel(
            name='Score',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField(help_text='Score from 1-10', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('comments', models.TextField(blank=True)),
                ('criteria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='judging.judgingcriteria')),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scores', to='judging.submission')),
            ],
            options={
                'unique_together': {('submission', 'criteria')},
            },
        ),
    ]
