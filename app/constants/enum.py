import enum

class GenderEnum(enum.Enum):
    male = "male"
    female = "female"
    intersex = "intersex"

class HandEnum(enum.Enum):
    left = "left"
    right = "right"

class FingerEnum(enum.Enum):
    thumb = "thumb"
    index = "index"
    middle = "middle"
    ring = "ring"
    pinky = "pinky"

class PatternEnum(enum.Enum):
    radial_loop = "radial_loop"
    ulnar_loop = "ulnar_loop"
    loop = "loop"
    whorl = "whorl"
    double_whorl = "double_whorl"
    arch = "arch"

class VolunteerStatuses(enum.Enum):
    pending = "pending"
    incompleted = "incompleted"
    completed = "completed"

class UserRoles(enum.Enum):
    admin = 'admin' # can do everything
    researcher = 'researcher' # almost everything, is the main user
    employee = 'employee' # just create patient and register fingerprints and other data less revelant
