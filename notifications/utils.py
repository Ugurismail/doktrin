from .models import Notification


def create_notification(user, notification_type, message, related_object_id=None):
    """Bildirim oluştur"""
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        message=message,
        related_object_id=related_object_id
    )


def notify_proposal_result(proposal, passed=True):
    """Öneri sonucu bildirimi"""
    from users.models import User

    notification_type = 'PROPOSAL_PASSED' if passed else 'PROPOSAL_REJECTED'
    status_text = 'kabul edildi' if passed else 'reddedildi'

    message = f'"{proposal.get_proposal_type_display()}" öneriniz {status_text}.'

    # Öneriyi oluşturan kişiye bildir
    create_notification(
        user=proposal.created_by,
        notification_type=notification_type,
        message=message,
        related_object_id=proposal.id
    )


def notify_new_proposal(proposal, target_users):
    """Yeni öneri bildirimi"""
    message = f'Yeni öneri: {proposal.get_proposal_type_display()}'

    for user in target_users:
        create_notification(
            user=user,
            notification_type='NEW_PROPOSAL',
            message=message,
            related_object_id=proposal.id
        )


def notify_comment_reply(comment, parent_comment):
    """Yoruma yanıt bildirimi"""
    message = f'{comment.user.username} yorumunuza yanıt verdi: "{comment.content[:50]}..."'

    create_notification(
        user=parent_comment.user,
        notification_type='COMMENT_REPLY',
        message=message,
        related_object_id=comment.id
    )


def notify_leader_change(organization, new_leader, organization_type):
    """Lider değişikliği bildirimi"""
    from users.models import User

    # Organizasyonun tüm üyelerine bildir
    if organization_type == 'TEAM':
        members = organization.members.all()
        org_name = organization.display_name
    elif organization_type == 'SQUAD':
        members = User.objects.filter(current_team__parent_squad=organization)
        org_name = organization.name
    elif organization_type == 'UNION':
        members = User.objects.filter(current_team__parent_squad__parent_union=organization)
        org_name = organization.name
    elif organization_type == 'PROVINCE_ORG':
        members = User.objects.filter(current_team__parent_squad__parent_union__parent_province_org=organization)
        org_name = organization.name
    else:
        return

    message = f'{org_name} için yeni lider: {new_leader.username}'

    for member in members:
        if member != new_leader:  # Yeni lidere kendisi için bildirim gönderme
            create_notification(
                user=member,
                notification_type='LEADER_CHANGE',
                message=message,
                related_object_id=organization.id
            )


def notify_formation_proposal(proposal, target_leaders):
    """Örgüt oluşturma önerisi bildirimi"""
    message = f'Yeni {proposal.level} oluşturma önerisi: {proposal.proposed_name}'

    for leader in target_leaders:
        create_notification(
            user=leader,
            notification_type='FORMATION_PROPOSAL',
            message=message,
            related_object_id=proposal.id
        )


def notify_formation_approved(organization, organization_type, members):
    """Örgüt oluşturuldu bildirimi"""
    if organization_type == 'SQUAD':
        org_type_text = 'Takım'
    elif organization_type == 'UNION':
        org_type_text = 'Birlik'
    elif organization_type == 'PROVINCE_ORG':
        org_type_text = 'İl Örgütü'
    else:
        return

    message = f'{org_type_text} oluşturuldu: {organization.name}'

    for member in members:
        create_notification(
            user=member,
            notification_type='FORMATION_APPROVED',
            message=message,
            related_object_id=organization.id
        )


def notify_announcement(announcement, target_users):
    """Duyuru bildirimi"""
    message = f'Yeni duyuru: {announcement.title}'

    for user in target_users:
        create_notification(
            user=user,
            notification_type='ANNOUNCEMENT',
            message=message,
            related_object_id=announcement.id
        )
