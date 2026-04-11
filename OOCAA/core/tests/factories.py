"""
Factory Boy factories for generating test data.
"""
import factory
from faker import Faker
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from core.models import SpaceObject, CDM, Event
from django.contrib.auth import get_user_model

User = get_user_model()
fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating test users."""
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'testuser{n}')
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        if not create:
            return
        if extracted is None:
            obj.set_password('defaultpass123')
        else:
            obj.set_password(extracted)


class SpaceObjectFactory(factory.django.DjangoModelFactory):
    """Factory for creating test space objects."""
    class Meta:
        model = SpaceObject

    object_designator = factory.Sequence(lambda n: f'{10000 + n}')
    object_name = factory.Faker('word')
    object_type = fake.random_element(['PAYLOAD', 'ROCKET BODY', 'DEBRIS', 'OTHER'])
    operator_organization = factory.Faker('company')
    maneuverable = False


class EventFactory(factory.django.DjangoModelFactory):
    """Factory for creating test events."""
    class Meta:
        model = Event

    obj1 = factory.SubFactory(SpaceObjectFactory)
    obj2 = factory.SubFactory(SpaceObjectFactory)
    representative_tca = factory.Faker('date_time', tzinfo=timezone.utc)


class CDMFactory(factory.django.DjangoModelFactory):
    """Factory for creating test CDM objects."""
    class Meta:
        model = CDM

    cdm_id = factory.Sequence(lambda n: f'CDM_{n:04d}')
    message_id = factory.Sequence(lambda n: f'MSG_{n:06d}')
    creation_date = factory.Faker('date_time', tzinfo=timezone.utc)
    ccsds_version = '1.0'
    originator = factory.Faker('company')
    
    obj1 = factory.SubFactory(SpaceObjectFactory)
    obj2 = factory.SubFactory(SpaceObjectFactory)
    
    tca = factory.LazyAttribute(lambda o: o.creation_date + timedelta(days=5))
    miss_distance_m = factory.Faker('pyfloat', left_digits=5, right_digits=2, positive=True)
    relative_speed_ms = factory.Faker('pyfloat', left_digits=2, right_digits=3, positive=True)
    collision_probability = Decimal('0.0000001')  # Fixed decimal value
    
    state_vector_obj1 = factory.LazyAttribute(lambda o: {
        'x_km': str(fake.pyfloat(left_digits=4, right_digits=2)),
        'y_km': str(fake.pyfloat(left_digits=4, right_digits=2)),
        'z_km': str(fake.pyfloat(left_digits=4, right_digits=2)),
        'x_dot_km_s': str(fake.pyfloat(left_digits=1, right_digits=3)),
        'y_dot_km_s': str(fake.pyfloat(left_digits=1, right_digits=3)),
        'z_dot_km_s': str(fake.pyfloat(left_digits=1, right_digits=3)),
    })
    
    state_vector_obj2 = factory.LazyAttribute(lambda o: {
        'x_km': str(fake.pyfloat(left_digits=4, right_digits=2)),
        'y_km': str(fake.pyfloat(left_digits=4, right_digits=2)),
        'z_km': str(fake.pyfloat(left_digits=4, right_digits=2)),
        'x_dot_km_s': str(fake.pyfloat(left_digits=1, right_digits=3)),
        'y_dot_km_s': str(fake.pyfloat(left_digits=1, right_digits=3)),
        'z_dot_km_s': str(fake.pyfloat(left_digits=1, right_digits=3)),
    })