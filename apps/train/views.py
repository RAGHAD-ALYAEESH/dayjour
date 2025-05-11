from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.models import CollaborationGroup, DataRecordOrDataset, AnalysisReport
import crypten
import torch
import pandas as pd
import os
from sklearn.model_selection import train_test_split
from torch.utils.data import TensorDataset, DataLoader
import shap
import matplotlib.pyplot as plt
from django.conf import settings


@login_required
def trainLocalmodel(request, pk):
    collaboration = get_object_or_404(CollaborationGroup, pk=pk, members=request.user)
    data_files = collaboration.dataset.filter(status='E')

    if not data_files.exists():
        messages.error(request, "No encrypted datasets available for training.")
        return redirect('collaboration_detail', pk=pk)

    try:
        crypten.init()
        input_size = 20  # Replace with actual number of features after decoding
        global_model = AMLModel(input_size)
        global_model.encrypt()

        # Prepare client data from uploaded encrypted files
        client_models = []
        client_sizes = []

        for ds in data_files:
            filepath = os.path.join(settings.MEDIA_ROOT, ds.file.name)
            enc_tensor = torch.load(filepath)

            # Decrypt just to count records (you can skip this if saved with metadata)
            plain = enc_tensor.get_plain_text()
            y = plain[:, -1]
            X = plain[:, :-1]
            client_sizes.append(len(X))

            # Re-encrypt split for training
            X_tensor = crypten.cryptensor(X)
            y_tensor = crypten.cryptensor(y.unsqueeze(1))
            client_model = AMLModel(input_size)
            client_model.encrypt()
            client_model.load_state_dict(global_model.state_dict())

            optimizer = crypten.optim.SGD(client_model.parameters(), lr=0.01)
            criterion = crypten.nn.BCEWithLogitsLoss()

            for _ in range(3):  # Few epochs per client
                outputs = client_model(X_tensor)
                loss = criterion(outputs, y_tensor)
                client_model.zero_grad()
                loss.backward()
                optimizer.step()

            client_models.append(client_model)

        # Federated averaging
        total = sum(client_sizes)
        avg_state = client_models[0].state_dict()
        for key in avg_state:
            avg_state[key] = sum(
                model.state_dict()[key] * (sz / total)
                for model, sz in zip(client_models, client_sizes)
            )
        global_model.load_state_dict(avg_state)

        # Save dummy analysis report to allow viewing insights
        for ds in data_files:
            AnalysisReport.objects.update_or_create(
                record=ds,
                defaults={'analysis_result': 'Training complete'}
            )

        messages.success(request, "Training completed successfully!")
        return redirect('collaboration_detail', pk=pk)

    except Exception as e:
        messages.error(request, f"Error during training: {str(e)}")
        return redirect('collaboration_detail', pk=pk)
    




def model_insights(request, pk):
    group = get_object_or_404(CollaborationGroup, pk=pk)
    data_records = group.dataset.filter(status='E')
    analysis = AnalysisReport.objects.filter(record__in=data_records).first()

    return render(request, 'model_insights.html', {
        'collaboration': group,
        'report': analysis,
    })


def download_shap_pdf(request, pk):
    group = get_object_or_404(CollaborationGroup, pk=pk, members=request.user)
    pdf_path = os.path.join(settings.MEDIA_ROOT, 'shap_report.pdf')
    if os.path.exists(pdf_path):
        return FileResponse(open(pdf_path, 'rb'), content_type='application/pdf', filename='shap_report.pdf')
    messages.error(request, "PDF not found. Generate insights first.")
    return redirect('collaboration_detail', pk=pk)


def view_trained_models(request):
    return render(request, 'view_trained_models.html')

def generate_shap_plot(model, X_sample, output_path):
    explainer = shap.Explainer(model, X_sample)
    shap_values = explainer(X_sample)

    # Waterfall plot (as an example)
    plt.figure()
    shap.plots.waterfall(shap_values[0], show=False)
    plt.savefig(output_path)
    plt.close()