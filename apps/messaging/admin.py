from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Conversation, Message, MessageReadStatus

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Administration des conversations"""
    
    list_display = [
        'id', 
        'get_participants_display', 
        'get_message_count',
        'get_product_link',
        'created_at', 
        'updated_at'
    ]
    list_filter = ['created_at', 'updated_at']
    search_fields = ['participants__username', 'participants__email']
    readonly_fields = ['created_at', 'updated_at', 'get_messages_preview']
    filter_horizontal = ['participants']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('participants', 'product')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Aperçu', {
            'fields': ('get_messages_preview',),
            'classes': ('collapse',)
        }),
    )
    
    def get_participants_display(self, obj):
        """Affiche les participants avec des badges colorés"""
        participants = obj.participants.all()
        html = ' '.join([
            f'<span class="badge badge-info" style="background-color: #17a2b8; color: white; padding: 3px 8px; border-radius: 3px; margin: 2px;">{p.username}</span>'
            for p in participants
        ])
        return format_html(html)
    get_participants_display.short_description = 'Participants'
    
    def get_message_count(self, obj):
        """Affiche le nombre de messages"""
        count = obj.messages.count()
        color = '#28a745' if count > 0 else '#6c757d'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} message{}</span>',
            color, count, 's' if count > 1 else ''
        )
    get_message_count.short_description = 'Messages'
    
    def get_product_link(self, obj):
        """Affiche un lien vers le produit si disponible"""
        if obj.product:
            return format_html(
                '<a href="/admin/shops/product/{}/change/" target="_blank">{}</a>',
                obj.product.id,
                obj.product.name if hasattr(obj.product, 'name') else f'Produit #{obj.product.id}'
            )
        return format_html('<span style="color: #6c757d;">-</span>')
    get_product_link.short_description = 'Produit'
    
    def get_messages_preview(self, obj):
        """Affiche un aperçu des derniers messages"""
        messages = obj.messages.order_by('-created_at')[:5]
        if not messages:
            return format_html('<p style="color: #6c757d;">Aucun message</p>')
        
        html = '<div style="max-height: 300px; overflow-y: auto;">'
        for msg in messages:
            html += f'''
            <div style="border-left: 3px solid #007bff; padding: 10px; margin: 10px 0; background: #f8f9fa;">
                <strong>{msg.sender.username}</strong>
                <small style="color: #6c757d; float: right;">{msg.created_at.strftime("%d/%m/%Y %H:%M")}</small>
                <br>
                <p style="margin: 5px 0;">{msg.content[:200]}{'...' if len(msg.content) > 200 else ''}</p>
                <span style="color: {'#28a745' if msg.is_read else '#dc3545'}; font-size: 12px;">
                    {'✓ Lu' if msg.is_read else '✗ Non lu'}
                </span>
            </div>
            '''
        html += '</div>'
        return format_html(html)
    get_messages_preview.short_description = 'Aperçu des messages'
    
    def get_queryset(self, request):
        """Optimise les requêtes"""
        qs = super().get_queryset(request)
        return qs.prefetch_related('participants', 'messages').annotate(
            message_count=Count('messages')
        )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Administration des messages"""
    
    list_display = [
        'id',
        'get_sender_display',
        'get_conversation_link',
        'get_content_preview',
        'is_read',
        'created_at'
    ]
    list_filter = ['is_read', 'created_at', 'sender']
    search_fields = ['sender__username', 'content', 'conversation__id']
    readonly_fields = ['created_at', 'get_full_content']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Message', {
            'fields': ('conversation', 'sender', 'get_full_content', 'attachment')
        }),
        ('Statut', {
            'fields': ('is_read',)
        }),
        ('Date', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_sender_display(self, obj):
        """Affiche l'expéditeur avec un badge"""
        return format_html(
            '<span style="background-color: #007bff; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            obj.sender.username
        )
    get_sender_display.short_description = 'Expéditeur'
    
    def get_conversation_link(self, obj):
        """Lien vers la conversation"""
        return format_html(
            '<a href="/admin/messaging/conversation/{}/change/">Conv. #{}</a>',
            obj.conversation.id,
            obj.conversation.id
        )
    get_conversation_link.short_description = 'Conversation'
    
    def get_content_preview(self, obj):
        """Aperçu du contenu"""
        preview = obj.content[:100] + ('...' if len(obj.content) > 100 else '')
        return format_html(
            '<span title="{}">{}</span>',
            obj.content,
            preview
        )
    get_content_preview.short_description = 'Contenu'
    
    def get_full_content(self, obj):
        """Affiche le contenu complet"""
        return format_html(
            '<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; max-width: 600px;">{}</div>',
            obj.content
        )
    get_full_content.short_description = 'Contenu complet'
    
    def get_queryset(self, request):
        """Optimise les requêtes"""
        qs = super().get_queryset(request)
        return qs.select_related('sender', 'conversation')
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        """Action pour marquer comme lu"""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} message(s) marqué(s) comme lu(s).')
    mark_as_read.short_description = "Marquer comme lu"
    
    def mark_as_unread(self, request, queryset):
        """Action pour marquer comme non lu"""
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} message(s) marqué(s) comme non lu(s).')
    mark_as_unread.short_description = "Marquer comme non lu"


@admin.register(MessageReadStatus)
class MessageReadStatusAdmin(admin.ModelAdmin):
    """Administration des statuts de lecture"""
    
    list_display = ['id', 'get_message_preview', 'user', 'read_at']
    list_filter = ['read_at', 'user']
    search_fields = ['user__username', 'message__content']
    readonly_fields = ['read_at']
    date_hierarchy = 'read_at'
    
    def get_message_preview(self, obj):
        """Aperçu du message"""
        preview = obj.message.content[:50] + ('...' if len(obj.message.content) > 50 else '')
        return format_html(
            '<a href="/admin/messaging/message/{}/change/">{}</a>',
            obj.message.id,
            preview
        )
    get_message_preview.short_description = 'Message'
    
    def get_queryset(self, request):
        """Optimise les requêtes"""
        qs = super().get_queryset(request)
        return qs.select_related('message', 'user')


# Personnalisation du site admin
admin.site.site_header = "Pi Market - Administration"
admin.site.site_title = "Pi Market Admin"
admin.site.index_title = "Tableau de bord"