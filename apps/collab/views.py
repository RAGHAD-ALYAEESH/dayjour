# ---- collab/views.py ----
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from apps.accounts.models import  CollaborationGroup, CompanyInvite, DataRecordOrDataset,AnalysisReport
from datetime import datetime
from apps.core.views import user_login ,home
from django.http import HttpResponse
from django.contrib.auth.models import User

def new_collaboration(request):
    # Only show companies who accepted the invite
    collab_partners = User.objects.filter(
    collaboration_groups__in=request.user.collaboration_groups.all()
    ).exclude(id=request.user.id)

    invited_partners = User.objects.filter(
    email__in=CompanyInvite.objects.filter(
        accepted=True,
        invited_by=request.user
    ).values_list('email', flat=True))

    companies_list = (collab_partners | invited_partners).distinct()
    
    user_datasets = DataRecordOrDataset.objects.filter(user=request.user)

    if request.method == 'POST':
        name = request.POST.get('collab_name')
        description = request.POST.get('objective')
        selected_company_ids = request.POST.getlist('companies')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        dataset_id = request.POST.get('dataset')
        new_company_names = request.POST.getlist('new_company_name[]')
        new_company_emails = request.POST.getlist('new_company_email[]')
        try:
           start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
           end_date_parsed = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except ValueError:
             messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
             return redirect('new_collaboration')

        if not name or not description:
            messages.error(request, "Please provide all required fields.")
            return redirect('new_collaboration')

        group = CollaborationGroup.objects.create(
        name=name,
        description=description,
        start_date=start_date_parsed,
        end_date=end_date_parsed,
        )
        
       # إضافة البيانات المشفرة
        if dataset_id:
            try:
                dataset = DataRecordOrDataset.objects.get(id=dataset_id)
                group.dataset.add(dataset)
            except DataRecordOrDataset.DoesNotExist:
                messages.error(request, "Dataset not found.")
                return redirect('new_collaboration')

        companies = User.objects.filter(id__in=selected_company_ids)
        group.members.add(*companies)

        group.members.add(request.user)

        for name, email in zip(new_company_names, new_company_emails):
           if name and email:
              invite = CompanyInvite.objects.create(
                  email=email,
                  name=name,
                  collaboration_group=group,
                  invited_by=request.user,
                  expiration_date=end_date_parsed,
              )

              accept_url = request.build_absolute_uri(invite.get_accept_url())
              reject_url = request.build_absolute_uri(invite.get_reject_url())

              subject = 'You are invited to join a collaboration!'
              message = render_to_string('emails/invite_email.html', {
                 'company_name': name,
                 'accept_url': accept_url,
                 'reject_url': reject_url,
                 'expiration_date': invite.expiration_date.strftime('%Y-%m-%d'),
                 'sender_name': request.user.get_full_name() or request.user.username,
                 })

              email_obj = EmailMessage(subject, message, to=[email])
              email_obj.content_subtype = "html"
              email_obj.send()


        messages.success(request, "Collaboration created successfully! Invitations have been sent if applicable.")
        return redirect('collaborations')

    return render(request, 'NewCollaboration.html', {
        'companies_list': companies_list,
        'user_datasets': user_datasets
    })

def accept_invite(request, token):
    invite = get_object_or_404(CompanyInvite, token=token)

    if invite.is_expired() or invite.accepted or invite.rejected:
        return HttpResponse("This invitation link is invalid or expired.")

    if request.method == 'POST':
        # Create User if doesn't exist
        user, created = User.objects.get_or_create(
            email=invite.email,
            defaults={'username': invite.email.split('@')[0], 'first_name': invite.name}
        )

        # Add user to collaboration group
        invite.collaboration_group.members.add(user)

        invite.accepted = True
        invite.save()
        messages.success(request, "Invitation accepted. You can now login.")

        return redirect('user_login')

    return render(request, 'invite/accept_invite.html', {'invite': invite})

def reject_invite(request, token):
    invite = get_object_or_404(CompanyInvite, token=token)

    if invite.is_expired() or invite.accepted or invite.rejected:
        return HttpResponse("This invitation link is invalid or expired.")

    invite.rejected = True
    invite.save()
    messages.success(request, "Invitation rejected.")
    return redirect('home')

@login_required(login_url='/en/login/')
def collaborations(request):
    user = request.user
    user_collaborations = CollaborationGroup.objects.filter(members=user).order_by('-created_at')
    
    return render(request, 'collaborations.html', {
        'collaborations': user_collaborations
    })

def collaboration_detail(request, pk):
    collaboration = get_object_or_404(CollaborationGroup, pk=pk, members=request.user)
    all_files = collaboration.dataset.all()

    # Check for any encrypted datasets
    has_encrypted_data = all_files.filter(status='E').exists()

    # Check for any analysis reports (indicating training success)
    has_analysis = AnalysisReport.objects.filter(record__in=all_files).exists()

    return render(request, 'collaboration_detail.html', {
        'collaboration': collaboration,
        'files': all_files,
        'has_encrypted_data': has_encrypted_data,
        'has_analysis': has_analysis,
    })

@login_required(login_url='/en/login/')
def delete_collaboration(request, pk):
    collaboration = get_object_or_404(CollaborationGroup, pk=pk, members=request.user)
    if request.method == 'POST':
        collaboration.delete()
        messages.success(request, 'Collaboration deleted successfully.')
        return redirect('collaborations')
    return render(request, 'confirm_delete.html', {'collaboration': collaboration})

@login_required(login_url='/en/login/')
def upload_collaboration_data(request, pk):
    collaboration = get_object_or_404(CollaborationGroup, pk=pk, members=request.user)

    # Get all encrypted datasets for this user
    user_datasets = DataRecordOrDataset.objects.filter(user=request.user, status='E', collaboration_groups__isnull=True)

    if request.method == 'POST':
        selected_file_id = request.POST.get('selected_file')
        if selected_file_id:
            try:
              dataset = DataRecordOrDataset.objects.get(id=selected_file_id, user=request.user)
              collaboration.dataset.add(dataset)
              messages.success(request, "Encrypted data linked to collaboration successfully.")
              return redirect('collaboration_detail', pk=pk)
            except DataRecordOrDataset.DoesNotExist:
              messages.error(request, "Selected dataset not found.")

    return render(request, 'upload_collab_data_select.html', {
        'collaboration': collaboration,
        'user_datasets': user_datasets
    })


