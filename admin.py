from django.contrib import admin
from mpi_intranet.events.models import (Event, InternalReservation,
                                        ExternalReservation, Attachment,
                                        Location, EventType, Speaker)
from reversion import VersionAdmin
from django.utils.html import format_html, format_html_join
from datetime import datetime
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.contrib import messages
from django import forms


class YearListFilter(admin.SimpleListFilter):
    title = 'year'
    parameter_name = 'year'

    def lookups(self, request, model_admin):
        events = Event.objects.all()\
            .values('start_date')\
            .extra(select={'year': 'EXTRACT(year FROM start_date)'})\
            .values('year').distinct()
        return ((int(event['year']), unicode(int(event['year'])), )
                for event in events)

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(start_date__year=self.value())


class TimeListFilter(admin.SimpleListFilter):
    title = 'time'
    parameter_name = 'time'

    def lookups(self, request, model_admin):
        return (
            (None, 'Current'),
            ('past', 'Show past'),
        )

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup}, []),
                'display': title}

    def queryset(self, request, queryset):
        if self.value() == 'past':
            return queryset.all()
        else:
            return queryset.filter(start_date__gte=datetime.now().date)


class ActiveListFilter(admin.SimpleListFilter):
    title = 'active'
    parameter_name = 'active'

    def lookups(self, request, model_admin):
        return (
            (None, 'Active'),
            ('inactive', 'Show inactive'),
        )

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup}, []),
                'display': title}

    def queryset(self, request, queryset):
        if self.value() == 'inactive':
            return queryset.all()
        else:
            return queryset.filter(is_active=True)


class LocationListFilter(admin.SimpleListFilter):
    title = 'location'
    parameter_name = 'location'

    def lookups(self, request, model_admin):
        locations = Event.objects.filter(
            is_inhouse=False).values('location_name_ext').distinct()
        location_list = ((None, 'All'), ('internal', 'MPI'), )
        for location in locations:
            location_list += ((location['location_name_ext'],
                               location['location_name_ext'], ), )
        return location_list

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup}, []),
                'display': title}

    def queryset(self, request, queryset):
        if self.value() == 'internal':
            return queryset.filter(is_inhouse=True)
        elif self.value():
            return queryset.filter(is_inhouse=False,
                                   location_name_ext=self.value())


class EventInternalReservationInline(admin.TabularInline):
    model = InternalReservation
    exclude = ('comment', )
    readonly_fields = ('edit_details', )
    extra = 0

    def edit_details(self, obj):
        if not obj.id:
            return ''
        return mark_safe(
            "<a href='%s' onclick='return showAddAnotherPopup(this);'>"
            "Details</a>" % reverse('admin:events_internalreservation_change',
                                    args=[obj.id]))


class EventExternalReservationInline(admin.TabularInline):
    model = ExternalReservation
    exclude = ('comment', )
    readonly_fields = ('edit_details', )
    extra = 0

    def edit_details(self, obj):
        if not obj.id:
            return ''
        return mark_safe(
            "<a href='%s' onclick='return showAddAnotherPopup(this);'>"
            "Details</a>" % reverse('admin:events_externalreservation_change',
                                    args=[obj.id]))


class AttachmentReservationInline(admin.TabularInline):
    model = Attachment
    readonly_fields = ('edit_details', )
    extra = 0

    def edit_details(self, obj):
        if not obj.id:
            return ''
        return mark_safe(
            "<a href='%s' onclick='return showAddAnotherPopup(this);'>"
            "Edit</a>" % reverse('admin:events_attachment_change',
                                 args=[obj.id]))


class EventAdminForm(forms.ModelForm):
    """
    Determine if:
      1. Total available seats is less than seats for internals only
      2. The start date is beyond the end date
    """
    model = Event

    def clean(self):
        if self.cleaned_data['is_inhouse']:
            if not self.cleaned_data['location_name_int']:
                raise forms.ValidationError({
                    'location_name_int': ['Specify location for internal event']
                })
        else:
            if not self.cleaned_data['location_name_ext']:
                raise forms.ValidationError({
                    'location_name_ext': ['Specify location for external event']
                })
        if 'seats_available' in self.cleaned_data and \
           'seats_for_internals_only' in self.cleaned_data:
            if self.cleaned_data['seats_available'] < self.cleaned_data['seats_for_internals_only']:
                raise forms.ValidationError({
                    'seats_available': ['Cannot be less than seats for internals'],
                    'seats_for_internals_only': ['Cannot be more than total seats available']
                })
        if 'start_date' in self.cleaned_data and 'end_date' in self.cleaned_data:
            if self.cleaned_data['start_date'] > self.cleaned_data['end_date']:
                raise forms.ValidationError({
                    'start_date': ['Cannot be ahead of end date'],
                    'end_date': ['Cannot be beyond of start date']
                })
        return super(EventAdminForm, self).clean()


@admin.register(Event)
class EventAdmin(VersionAdmin):
    model = Event
    form = EventAdminForm

    fieldsets = [
        (None, {'fields': [
            'title', 'is_active', 'type', 'speakers', 'topic', 'start_date',
            'end_date', 'person_in_charge', 'is_inhouse', 'location_name_int',
            'location_name_ext', 'location_building_ext', 'location_room_ext',
            'location_contact_ext', 'short_description', 'full_description',
            'notes', 'casy_ref', 'seats_available', 'seats_for_internals_only'
        ]}),
    ]
    list_display = ['is_active', 'get_date', 'type', 'title',
                    'person_in_charge', 'get_speakers', 'get_location',
                    'get_room', 'get_remark', 'get_casymir_project', 'get_info']

    search_fields = ['title', 'topic', 'short_description', 'full_description']
    list_filter = [YearListFilter, 'type', TimeListFilter, LocationListFilter,
                   ActiveListFilter]
    list_display_links = ['title']
    inlines = [EventInternalReservationInline, EventExternalReservationInline,
               AttachmentReservationInline]
    save_as = True

    def get_queryset(self, request):
        """
        Here we introduce custom sortable columns:
        1. Location name
        2. Room name
        3. Remarks existence
        TODO: replace with conditional annotations after the project will be
              upgraded to Django 1.8.x
        """
        qs = super(EventAdmin, self).get_queryset(request)
        qs = qs\
            .extra(select={
                'location_name': """
                    CASE is_inhouse
                        WHEN TRUE THEN 'MPI'
                        ELSE location_name_ext
                    END
                """
            })\
            .extra(select={
                'room_name': """
                    CASE is_inhouse
                        WHEN TRUE THEN (
                            SELECT name FROM events_location
                                WHERE events_location.id=location_name_int_id)
                        ELSE location_room_ext
                    END
                """
            })\
            .extra(select={
                'remarks_existence': """
                    CASE notes
                        WHEN '' THEN FALSE
                        WHEN NULL THEN FALSE
                        ELSE TRUE
                    END
                """
            })
        return qs

    def get_date(self, obj):
        """
        Start and end dates ot an event
        """
        return format_html('{} - {}',
                           obj.start_date.strftime('%Y-%m-%d'),
                           obj.end_date.strftime('%Y-%m-%d'))
    get_date.short_description = 'Date'
    get_date.admin_order_field = 'start_date'

    def get_speakers(self, obj):
        """
        Event speakers list
        """
        if not obj.type.has_speakers:
            return ''
        return format_html_join(
            '', '{}<br/>', ((speaker.__unicode__(), )
                            for speaker in obj.speakers.all()))
    get_speakers.short_description = 'Speakers'

    def get_location(self, obj):
        """
        Location name, for internal it will be 'MPI'
        """
        if obj.is_inhouse:
            return 'MPI'
        else:
            return obj.location_name_ext
    get_location.short_description = 'Location'
    get_location.admin_order_field = 'location_name'

    def get_room(self, obj):
        """
        Room name - a classroom or any other room
        """
        if obj.is_inhouse:
            return obj.location_name_int if obj.location_name_int else ''
        else:
            return obj.location_room_ext
    get_room.short_description = 'Room'
    get_room.admin_order_field = 'room_name'

    def get_remark(self, obj):
        """
        Check if there are notes on an event
        """
        return True if obj.notes else False
    get_remark.short_description = 'Remark'
    get_remark.boolean = True
    get_remark.admin_order_field = 'remarks_existence'

    def get_casymir_project(self, obj):
        """
        Casymir reference
        """
        return format_html('{}', obj.casy_ref)
    get_casymir_project.short_description = 'CASYMIR project'
    get_casymir_project.admin_order_field = 'casy_ref'

    def get_info(self, obj):
        """
        Notifications for teh last column 'Info'
        TODO: replace text with icons when we will have icons
        """
        info_list = []
        if obj.is_available():
            info_list.append('Seats available')
        if obj.is_waiting():
            info_list.append('People are waiting for confirmation')
        if obj.is_overbooked():
            info_list.append('Event is overbooked')
        return '<br/><br/>'.join(info_list)
    get_info.short_description = 'Info'
    get_info.allow_tags = True

    def change_view(self, request, object_id, form_url='', extra_context=None):     # pylint: disable=E0202
        """
        Determine if:
          1. An event is overbooked
          2. There are people waiting for reservation confirmation
        """
        try:
            obj = Event.objects.get(id=object_id)
        except Event.DoesNotExist:
            pass
        else:
            if obj.is_overbooked():
                messages.warning(request, 'Event is now overbooked')
            if obj.is_waiting():
                messages.warning(request, 'There are registrations waiting for confirmation')
            list(messages.get_messages(request))    # Clear messages
        return super(EventAdmin, self).change_view(request, object_id, form_url,
                                                   extra_context=extra_context)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    pass


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    pass


@admin.register(InternalReservation)
class InternalReservationAdmin(admin.ModelAdmin):
    list_display = ['event', 'is_confirmed', 'casy_ref']
    list_display_links = ['event']


@admin.register(ExternalReservation)
class ExternalReservationAdmin(admin.ModelAdmin):
    list_display = ['event', 'is_confirmed', 'casy_ref']
    list_display_links = ['event']


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    pass
