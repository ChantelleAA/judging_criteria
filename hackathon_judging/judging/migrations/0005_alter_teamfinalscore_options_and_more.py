# Generated by Django 5.2.3 on 2025-07-03 16:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('judging', '0004_publicjudgment'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='teamfinalscore',
            options={'ordering': ['-final_weighted_score', 'team__name'], 'verbose_name': 'Team Final Score', 'verbose_name_plural': 'Team Final Scores'},
        ),
        migrations.RenameField(
            model_name='publicjudgment',
            old_name='comment_business_viability',
            new_name='comment_presentation_and_originality',
        ),
        migrations.RenameField(
            model_name='publicjudgment',
            old_name='comment_innovation',
            new_name='comment_quantum_computing_quality',
        ),
        migrations.RenameField(
            model_name='publicjudgment',
            old_name='comment_presentation',
            new_name='comment_quantum_computing_relevance',
        ),
        migrations.RenameField(
            model_name='publicjudgment',
            old_name='comment_quantum_tech',
            new_name='comment_social_impact_based_on_sdgs',
        ),
        migrations.RenameField(
            model_name='publicjudgment',
            old_name='presentation',
            new_name='presentation_and_originality',
        ),
        migrations.RenameField(
            model_name='publicjudgment',
            old_name='quantum_tech_quality',
            new_name='quantum_computing_quality',
        ),
        migrations.RenameField(
            model_name='publicjudgment',
            old_name='innovation',
            new_name='quantum_computing_relevance',
        ),
        migrations.RenameField(
            model_name='publicjudgment',
            old_name='social_impact',
            new_name='social_impact_based_on_sdgs',
        ),
        migrations.RenameField(
            model_name='teamfinalscore',
            old_name='business_viability_score',
            new_name='presentation_and_originality',
        ),
        migrations.RenameField(
            model_name='teamfinalscore',
            old_name='innovation_score',
            new_name='quantum_computing_quality',
        ),
        migrations.RenameField(
            model_name='teamfinalscore',
            old_name='presentation_score',
            new_name='quantum_computing_relevance',
        ),
        migrations.RenameField(
            model_name='teamfinalscore',
            old_name='quantum_tech_score',
            new_name='social_impact_based_on_sdgs',
        ),
        migrations.RemoveField(
            model_name='publicjudgment',
            name='business_viability',
        ),
        migrations.RemoveField(
            model_name='publicjudgment',
            name='comment_social_impact',
        ),
        migrations.RemoveField(
            model_name='teamfinalscore',
            name='social_impact_score',
        ),
    ]
