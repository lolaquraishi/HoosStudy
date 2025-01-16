from django.contrib import admin

from .models import Course, User, Document, Keyword, Message, MessageBoard, UserCoursePreference

class CourseAdmin(admin.ModelAdmin):
    list_display = ('mnemonic', 'number', 'title')
    list_filter = (['mnemonic'])

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'author', 'course', 'file', 'get_keywords')
    list_filter = (['author', 'course'])

    def get_keywords(self, obj):
        return ", ".join([keyword.name for keyword in obj.keywords.all()])

    get_keywords.short_description = 'Keywords'

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'year', 'is_pma_admin')
    list_filter = (['year', 'is_pma_admin'])

class KeywordAdmin(admin.ModelAdmin):
    list_display = ('name',)

class MessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'timestamp', 'message_board')
    list_filter = (['user', 'message_board'])

class MessageBoardAdmin(admin.ModelAdmin):
    list_display = ('course', 'course')


from .models import StudySessionAttendee
from .models import StudySessionLocation
from .models import StudySession
from .models import StudySessionAvailability
from .models import JoinRequest

# Register your models here.

#all tables used in admin area

admin.site.register(StudySessionAttendee)
admin.site.register(StudySessionLocation)
admin.site.register(StudySession)
admin.site.register(StudySessionAvailability)
admin.site.register(JoinRequest)
admin.site.register(Course, CourseAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Keyword, KeywordAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(MessageBoard, MessageBoardAdmin)
admin.site.register(UserCoursePreference)