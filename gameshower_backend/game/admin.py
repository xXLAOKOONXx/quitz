from django.contrib import admin

from .models import Game, GameParticipant, JepardyColumn, JepardyQuestion, JepardyTable, GameQuestion, CurrentView

# Register your models here.
admin.site.register(Game)
admin.site.register(GameParticipant)
admin.site.register(JepardyColumn)
admin.site.register(JepardyQuestion)
admin.site.register(JepardyTable)
admin.site.register(GameQuestion)
admin.site.register(CurrentView)
