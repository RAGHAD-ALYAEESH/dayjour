# ---- dataset/views.py ----
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import os
import pandas as pd
import torch
import crypten
from sklearn.preprocessing import LabelEncoder
from apps.accounts.models import DataRecordOrDataset

# Flag لتفادي إعادة التهيئة
crypten_initialized = False

def initialize_crypten():
    global crypten_initialized
    if not crypten_initialized:
        crypten.init_thread(rank=0, world_size=1)
        crypten_initialized = True

def encrypt_dataframe(df):
    df_encoded = df.copy()

    # ترميز الأعمدة النصية
    for col in df_encoded.select_dtypes(include=['object', 'string']).columns:
        le = LabelEncoder()
        try:
            df_encoded[col] = le.fit_transform(df_encoded[col])
        except Exception as e:
            raise ValueError(f"خطأ في ترميز العمود '{col}': {str(e)}")

    # تحويل كل البيانات إلى float32
    tensor = torch.tensor(df_encoded.values, dtype=torch.float32)
    return crypten.cryptensor(tensor)

@login_required(login_url='/en/login/')
def upload(request):
    if request.method == 'POST' and request.FILES.get('dataFile'):
        uploaded_file = request.FILES['dataFile']
        file_path = default_storage.save(f"uploads/{uploaded_file.name}", uploaded_file)

        full_path = os.path.join(settings.MEDIA_ROOT, file_path)

        try:
            # 1. تهيئة CrypTen مرة واحدة
            initialize_crypten()

            # 2. قراءة الملف
            df = pd.read_csv(full_path)

            # 3. تشفير البيانات
            encrypted_tensor = encrypt_dataframe(df)

            # 4. حفظ البيانات المشفرة كـ .pt
            encrypted_path = file_path.replace(".csv", "_encrypted.pt")
            torch.save(encrypted_tensor, os.path.join(settings.MEDIA_ROOT, encrypted_path))

            # 5. إنشاء سجل في قاعدة البيانات مع الإشارة إلى ملف البيانات المشفرة
            DataRecordOrDataset.objects.create(
                user=request.user,
                status='E',
                file=encrypted_path
            )

            return redirect('uploaded_data')
        except Exception as e:
            messages.error(request, f"حدث خطأ أثناء التشفير: {str(e)}")
            return redirect('upload_data')

    return render(request, 'uploadData.html')

@login_required(login_url='/en/login/')
def uploaded_data(request):
    user = request.user
    uploaded_files = DataRecordOrDataset.objects.filter(user=user).order_by('-recorded_at')
    return render(request, 'uploaded_data.html', {'uploaded_files': uploaded_files})

@login_required(login_url='/en/login/')
def delete_uploaded_file(request, pk):
    file = get_object_or_404(DataRecordOrDataset, pk=pk, user=request.user)

    if file.file:
        default_storage.delete(file.file.name)  # Delete the actual file

    file.delete()  # Delete the database entry
    messages.success(request, "File deleted successfully.")
    return redirect('uploaded_data')