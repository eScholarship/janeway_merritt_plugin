# Generated by Django 3.2.18 on 2023-10-16 22:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('repository', '0035_alter_preprintaccess_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='MerrittQueue',
            fields=[
                ('preprint', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='repository.preprint')),
                ('queue_date', models.DateTimeField()),
                ('completion_date', models.DateTimeField(null=True)),
                ('status', models.CharField(choices=[('W', 'Item to be processed'), ('P', 'Sending the item to Merritt'), ('C', 'Item processed successfully'), ('E', 'Item failed')], default='W', max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name='RepoMerrittSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('merritt_collection', models.CharField(max_length=30)),
                ('scan_date', models.DateTimeField(null=True)),
                ('repo', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='repository.repository')),
            ],
        ),
        migrations.CreateModel(
            name='PreprintMerrittRequests',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_date', models.DateTimeField()),
                ('request_detail', models.CharField(max_length=3000, null=True)),
                ('response', models.CharField(max_length=3000, null=True)),
                ('status', models.CharField(choices=[('P', 'Preparing to send'), ('PR', 'Error before sending'), ('S', 'Sent request'), ('SR', 'Error sending request'), ('D', 'Callback with success received'), ('E', 'Callback with failure received')], default='P', max_length=2)),
                ('preprint', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='repository.preprint')),
            ],
        ),
        migrations.CreateModel(
            name='MerrittJobStatus',
            fields=[
                ('job_id', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('callback_date', models.DateTimeField()),
                ('callback_response', models.CharField(max_length=3000)),
                ('status', models.CharField(choices=[('C', 'Job completed successfully'), ('E', 'Job failed')], default='E', max_length=1)),
                ('preprint', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='repository.preprint')),
            ],
        ),
    ]
