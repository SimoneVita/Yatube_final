from django.shortcuts import render


def server_error(request):
    return render(request, 'core/500.html', {'path': request.path}, status=500)

def page_not_found(request, exception):
    return render(request, 'core/404.html', {'path': request.path}, status=404)

def permission_denied_view(request, reason=''):
    return render(request, 'core/403csrf.html')
