from django.db import models
from filer.fields.file import FilerFileField
from djangocms_text_ckeditor.fields import HTMLField
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from mpi_intranet.base.email import send
from mpi_intranet.base.casymir import get_employee


class Event(models.Model):
    """
    Events that are hosted by the MPI Luxembourg
    """

    # the title of the event that will be displayed publically
    title = models.CharField(max_length=64)

    # Whether this event is active or not. Inactive events won't appear on the MPI Intranet and can't receive
    # reservations
    is_active = models.BooleanField(default=True)

    # The event type
    type = models.ForeignKey('EventType', limit_choices_to={'is_active': True}, on_delete=models.PROTECT)

    # The speakers
    speakers = models.ManyToManyField('Speaker', blank=True, null=True)

    # The topic (depends on the type whethe the event has a topic or not)
    topic = models.CharField(max_length=128, blank=True, null=True)

    # The Start date of the event (inclusive)
    start_date = models.DateTimeField()

    # The End date of the event (inclusive)
    end_date = models.DateTimeField()

    # The Person in Charge for this event
    person_in_charge = models.CharField(max_length=64, blank=True, null=True)

    # Whether or not the location for this event is inhouse
    is_inhouse = models.BooleanField(default=True)

    # The location for inhouse events
    location_name_int = models.ForeignKey('Location', blank=True, null=True)

    # The location name for external events
    location_name_ext = models.CharField(max_length=64, blank=True, null=True)

    # The location address for external events
    location_building_ext = models.CharField(max_length=65, blank=True, null=True)

    # The room at the location for external events
    location_room_ext = models.CharField(max_length=16, blank=True, null=True)

    # The Details of the contact for external events (name, phone, email)
    location_contact_ext = models.CharField(max_length=128, blank=True, null=True)

    # The short description of this event, to be displayed on the list of upcoming events
    short_description = models.CharField(max_length=256, blank=True, null=True)

    # The full description of this event, to be displayed on the full detail list
    full_description = HTMLField(configuration="CKEDITOR_SETTINGS")

    # Where the event manager can add some notes to the event.
    notes = models.TextField(blank=True, null=True)

    # Casymir ref for this event.
    casy_ref = models.IntegerField()

    # Number of seats for this event (only needed when internal or external reservations are allowed)
    seats_available = models.IntegerField(null=True)

    # Number of seats for this event reserved for internals (only needed when internal or
    # external reservations are allowed)
    seats_for_internals_only = models.IntegerField(null=True)

    @property
    def location_full(self):
        """
        Full location as single string
        """
        location_and_room = "%s, %s" % (
            "MPI" if self.is_inhouse else self.location_name_ext,
            self.location_name_int if self.is_inhouse else self.location_room_ext, )
        building_and_contact = ""
        if self.location_building_ext:
            building_and_contact += self.location_building_ext
        if self.location_contact_ext:
            building_and_contact += ", " if len(building_and_contact) else ""
            building_and_contact += self.location_contact_ext
        return "%s, %s" % (location_and_room, building_and_contact) if building_and_contact.strip() else \
            "%s" % location_and_room

    def __unicode__(self):  # pragma: no cover
        return self.title

    def save(self, *args, **kwargs):
        if self.id:
            if not self.type.allow_internal_registrations:
                if self.internal_reservations.all():
                    self.internal_reservations.all().delete()
            if not self.type.allow_external_registrations:
                if self.external_reservations.all():
                    self.external_reservations.all().delete()
            if not self.type.has_speakers:
                self.speakers.clear()
        if self.is_inhouse:
            self.location_name_ext = None
            self.location_building_ext = None
            self.location_room_ext = None
            self.location_contact_ext = None
        else:
            self.location_name_int = None
        if not self.type.has_topic:
            self.topic = None
        super(Event, self).save(*args, **kwargs)

    def is_overbooked(self):
        """
        Check if event is overbooked
        """
        int_seats = self.seats_for_internals_only
        ext_seats = self.seats_available - self.seats_for_internals_only
        int_confirmed = self.internal_reservations.filter(is_confirmed=True).count()
        ext_confirmed = self.external_reservations.filter(is_confirmed=True).count()
        if int_seats < int_confirmed or ext_seats < ext_confirmed:
            return True
        else:
            return False

    def is_waiting(self):
        """
        Check if event has waiting confirmations
        """
        int_seats = self.seats_for_internals_only
        ext_seats = self.seats_available - self.seats_for_internals_only
        int_confirmed = self.internal_reservations.filter(is_confirmed=True).count()
        ext_confirmed = self.external_reservations.filter(is_confirmed=True).count()
        int_unconfirmed = self.internal_reservations.filter(is_confirmed=False).count()
        ext_unconfirmed = self.external_reservations.filter(is_confirmed=False).count()
        if int_unconfirmed > 0 and int_confirmed < int_seats or \
           ext_unconfirmed > 0 and ext_confirmed < ext_seats:
            return True
        else:
            return False

    def is_available(self):
        """
        Check if event has free seats
        """
        int_seats = self.seats_for_internals_only
        ext_seats = self.seats_available - self.seats_for_internals_only
        int_all = self.internal_reservations.count()
        ext_all = self.external_reservations.count()
        if int_seats > int_all or ext_seats > ext_all:
            return True
        else:
            return False


class Location(models.Model):
    """
    Names of locations at the MPI Luxemburg (e.g. 'Room 245')
    """

    # The displayable name of this location
    name = models.CharField(max_length=64, unique=True)

    def __unicode__(self):  # pragma: no cover
        return self.name


class EventType(models.Model):
    """
    The event type. Event types set the appearance of the event on the intranet pages and set whether or not
    registrations are allowed. They can be deactivated so that no event can be created anymore based on this
    type.
    """

    # the name to be displayed in drop down boxes. Used for admin only
    name = models.CharField(max_length=32, unique=True)

    # the Title to be displayed on the web pages
    title = models.CharField(max_length=128)

    # Whether the type can be used for (new) events
    is_active = models.BooleanField(default=True)

    # Whether to allow registrations from MPI employees or not
    allow_internal_registrations = models.BooleanField(default=True)

    # Whether to allow registrations from externals
    allow_external_registrations = models.BooleanField(default=True)

    # Whether the event can has speakers or not
    has_speakers = models.BooleanField(default=False)

    # Whether the event has a topic or not
    has_topic = models.BooleanField(default=False)

    def __unicode__(self):  # pragma: no cover
        return self.name


class Speaker(models.Model):
    """
    A speaker of an event
    """

    # the id of this speakers entry on the casymir database
    casy_ref = models.IntegerField(unique=True)

    # the biography that will be displayed with the event details
    bio = models.TextField()

    def __unicode__(self):  # pragma: no cover
        # TODO resolve the full name of the speaker
        return unicode(self.casy_ref)


class Reservation(models.Model):
    """
    The abstract reservation class
    """

    # a casymir reference number
    casy_ref = models.IntegerField()

    # Whether the reservation is confirmed or the registrant is waiting for a seat
    is_confirmed = models.BooleanField(default=True)

    # A place for the event manager to leave an internal comment for this reservation
    comment = models.TextField()

    class Meta(object):
        abstract = True


class InternalReservation(Reservation):
    """
    A reservation by a employee of the MPI. casy_ref points to a 'PersonalNummer' in casymir.
    """

    event = models.ForeignKey('Event', related_name='internal_reservations')

    def __unicode__(self):  # pragma: no cover
        # TODO resolve the full name of the internal participant
        return str(self.casy_ref)


class ExternalReservation(Reservation):
    """
    A reservation by an external of the MPI. casy_ref points to a '... (TBD)' in casymir.
    """

    event = models.ForeignKey('Event', related_name='external_reservations')

    def __unicode__(self):  # pragma: no cover
        # TODO resolve the full name of the external participant
        return str(self.casy_ref)


class Attachment(models.Model):
    """
    A file attachment to the event. It will be downloadable from the MPI Intranet
    """
    # In accordance with spec we need title here
    title = models.CharField(max_length=128)

    # the file that contains the attachment (pdf, xls, ...)
    file = FilerFileField()

    # the event that this attachment belongs to
    event = models.ForeignKey('Event', related_name='attachments')

    def __unicode__(self):  # pragma: no cover
        return self.title


@receiver(pre_save, sender=Event, dispatch_uid="event_save_signal")
def event_save(sender, instance, using, **kwargs):  # pylint: disable=W0613,R0912
    """
    Send e-mails to all people registered to an event with updated dates or
    cancel notification
    """
    def dates_updated(registration):
        """
        Dates have been updated
        """
        employee = get_employee(registration.casy_ref)
        if employee and employee["email"]:
            salut = " ".join([employee["salutation_short"], employee["firstname"], employee["lastname"]])
            send("test",
                 (employee["email"], ),
                 {"msg": "%s\nDates of the event have been changed to: %s - %s" % (
                     salut, instance.start_date, instance.end_date, )})

    def event_canceled(registration):
        """
        Event has been canceled
        """
        employee = get_employee(registration.casy_ref)
        if employee and employee["email"]:
            salut = " ".join([employee["salutation_short"], employee["firstname"], employee["lastname"]])
            send("test", (employee["email"], ),
                 {"msg": "%s\nThis event has been canceled" % salut})

    def event_activated(registration):
        """
        Event has been activated
        """
        employee = get_employee(registration.casy_ref)
        if employee and employee["email"]:
            salut = " ".join([employee["salutation_short"], employee["firstname"], employee["lastname"]])
            send("test", (employee["email"], ),
                 {"msg": "%s\nThis event will be performed" % salut})

    def location_updated(registration):
        """
        Location has been updated
        """
        employee = get_employee(registration.casy_ref)
        if employee and employee["email"]:
            salut = " ".join([employee["salutation_short"], employee["firstname"], employee["lastname"]])
            send("test", (employee["email"], ),
                 {"msg": "%s\nLocation of the event has been changed to: %s" % (salut, instance.location_full, )})

    if instance.pk:
        obj = Event.objects.get(pk=instance.pk)
        if instance.start_date != obj.start_date or instance.end_date != obj.end_date:
            for registration in InternalReservation.objects.filter(event=instance):
                dates_updated(registration)
            for registration in ExternalReservation.objects.filter(event=instance):
                dates_updated(registration)
        elif instance.is_active != obj.is_active:
            if instance.is_active:
                for registration in InternalReservation.objects.filter(event=instance):
                    event_activated(registration)
                for registration in ExternalReservation.objects.filter(event=instance):
                    event_activated(registration)
            else:
                for registration in InternalReservation.objects.filter(event=instance):
                    event_canceled(registration)
                for registration in ExternalReservation.objects.filter(event=instance):
                    event_canceled(registration)
        elif instance.location_full != obj.location_full:
            for registration in InternalReservation.objects.filter(event=instance):
                location_updated(registration)
            for registration in ExternalReservation.objects.filter(event=instance):
                location_updated(registration)


@receiver(pre_save, sender=InternalReservation,
          dispatch_uid="internal_registration_save_signal")
@receiver(pre_save, sender=ExternalReservation,
          dispatch_uid="external_registration_save_signal")
def registration_save(sender, instance, using, **kwargs):   # pylint: disable=W0613
    """
    Send new registration or registration status update email to registered
    person
    """
    if not instance.pk:
        employee = get_employee(instance.casy_ref)
        if employee and employee["email"]:
            salut = " ".join([employee["salutation_short"], employee["firstname"], employee["lastname"]])
            send("test",
                 (employee["email"], ),
                 {"msg": "%s\nYou have new registration with status %s" % (
                     salut, "Confirmed" if instance.is_confirmed else "Waiting", )})
    else:
        try:
            obj = InternalReservation.objects.get(pk=instance.pk)
        except InternalReservation.DoesNotExist:
            obj = ExternalReservation.objects.get(pk=instance.pk)
        if instance.is_confirmed != obj.is_confirmed:
            employee = get_employee(instance.casy_ref)
            if employee and employee["email"]:
                salut = " ".join([employee["salutation_short"], employee["firstname"], employee["lastname"]])
                send("test",
                     (employee["email"], ),
                     {"msg": "%s\nStatus of your registration has been changed to %s" % (
                         salut, "Confirmed" if instance.is_confirmed else "Waiting", )})


@receiver(pre_delete, sender=InternalReservation,
          dispatch_uid="internal_registration_delete_signal")
@receiver(pre_delete, sender=ExternalReservation,
          dispatch_uid="external_registration_delete_signal")
def registration_delete(sender, instance, using, **kwargs):     # pylint: disable=W0613
    """
    Send e-mail notification about registration deletion to previously
    registered person
    """
    employee = get_employee(instance.casy_ref)
    if employee and employee["email"]:
        salut = " ".join([employee["salutation_short"], employee["firstname"], employee["lastname"]])
        send("test", (employee["email"], ),
             {"msg": "%s\nYour registration has been deleted" % salut})
