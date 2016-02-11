from django.conf.urls import url

urlpatterns = [
    url(r'^event_type/(?P<event_type_id>\d+)/',
        'mpi_intranet.events.views.get_event_type', name='event_type'),
    url(r'^', 'mpi_intranet.events.views.events', name='events')
]
