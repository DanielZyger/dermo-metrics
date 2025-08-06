import enum

class GenderEnum(enum.Enum):
    male = "male"
    female = "female"
    other = "other"

class HandEnum(enum.Enum):
    left = "left"
    right = "right"

class FingerEnum(enum.Enum):
    thumb = "thumb"
    index = "index"
    middle = "middle"
    ring = "ring"
    little = "little"

class PatternEnum(enum.Enum):
    loop = "loop"
    whorl = "whorl"
    arch = "arch"

class UserRoles(enum.Enum):
    admin = 'admin' # can do everything
    researcher = 'researcher' # almost everything, is the main user
    employee = 'employee' # just create patient and register fingerprints and other data less revelant
