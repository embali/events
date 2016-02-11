from django.shortcuts import render
from mpi_intranet.base.authentication import login_required
from django.http import JsonResponse
from mpi_intranet.events.models import EventType


@login_required
def events(request):
    return render(request, 'events.html')


def get_event_type(request, event_type_id):     # pylint: disable=W0613
    """
    Returns event type options:
    1. Has speakers
    2. Has topic
    """
    try:
        event_type = EventType.objects.get(id=event_type_id)
        return JsonResponse({
            "allow_internal_registrations": event_type.allow_internal_registrations,
            "allow_external_registrations": event_type.allow_external_registrations,
            "has_speakers": event_type.has_speakers,
            "has_topic": event_type.has_topic})
    except EventType.DoesNotExist:
        return JsonResponse({
            "allow_internal_registrations": True,
            "allow_external_registrations": True,
            "has_speakers": False,
            "has_topic": False})
