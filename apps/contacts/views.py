from django.contrib import messages
from django.shortcuts import redirect, render

from .models import ContactMessage


def contact_page(request):
    if request.method == 'POST':
        ContactMessage.objects.create(
            name=request.POST.get('name', '').strip(),
            email=request.POST.get('email', '').strip(),
            subject=request.POST.get('subject', '').strip(),
            message=request.POST.get('message', '').strip(),
        )
        messages.success(request, 'Your message has been sent successfully.')
        return redirect('contacts:contact')
    return render(request, 'contacts/contact.html')

# Create your views here.
