from django.db import models
from .spaceobject import SpaceObject
class Event(models.Model):
    """Model representing a conjunction event grouping related CDMs."""
    
    # Store the canonical pair of space objects for this event
    obj1 = models.ForeignKey(
        SpaceObject,
        related_name='events_as_obj1',
        on_delete=models.CASCADE,
    )
    obj2 = models.ForeignKey(
        SpaceObject,
        related_name='events_as_obj2',
        on_delete=models.CASCADE,
    )
    
    # Store representative TCA
    representative_tca = models.DateTimeField()
    
    class Meta:
        # Ensure we don't duplicate events for the same object pair
        constraints = [
            models.UniqueConstraint(
                fields=['obj1', 'obj2', 'representative_tca'],
                name='unique_event_per_conjunction'
            )
        ]
        indexes = [
            models.Index(fields=['obj1', 'obj2', 'representative_tca']),
        ]
    
    def __str__(self):
        return f"Event {self.id}: {self.obj1.object_designator} & {self.obj2.object_designator} @ {self.representative_tca}"