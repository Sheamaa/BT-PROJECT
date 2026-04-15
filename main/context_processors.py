def notifications_processor(request):
    if request.user.is_authenticated:
        try:
            notifications = request.user.notifications.order_by('-created_at')[:5]
            unread_count = request.user.notifications.filter(is_read=False).count()
            return {
                'notifications': notifications,
                'unread_count': unread_count
            }
        except:
            return {}
    return {}