from django.db import models
from django.conf import settings
from datetime import datetime, timedelta


class Activity(models.Model):
    """Global Aktivite Feed"""
    ACTIVITY_TYPE_CHOICES = [
        ('proposal_created', 'Öneri Oluşturuldu'),
        ('proposal_passed', 'Öneri Kabul Edildi'),
        ('proposal_rejected', 'Öneri Reddedildi'),
        ('comment_added', 'Yorum Eklendi'),
        ('vote_cast', 'Oy Kullanıldı'),
        ('leader_changed', 'Lider Değişti'),
        ('organization_formed', 'Organizasyon Oluşturuldu'),
        ('team_created', 'Ekip Oluşturuldu'),
        ('prediction_created', 'Tahmin Oluşturuldu'),
        ('prediction_expired', 'Tahmin Süresi Doldu'),
        ('prediction_verified', 'Tahmin Doğrulandı'),
    ]

    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPE_CHOICES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    description = models.TextField()
    related_url = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Activities'

    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()}"


class ProposalDraft(models.Model):
    """Öneri Taslağı - Kaydet ve sonra gönder"""
    PROPOSAL_TYPE_CHOICES = [
        ('NEW_ARTICLE', 'Yeni Madde'),
        ('AMEND_ARTICLE', 'Madde Değişikliği'),
        ('REPEAL_ARTICLE', 'Madde İptali'),
        ('RENAME_ARTICLE', 'İsim Değişikliği'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='proposal_drafts')
    proposal_type = models.CharField(max_length=20, choices=PROPOSAL_TYPE_CHOICES)
    related_article = models.ForeignKey('DoctrineArticle', on_delete=models.CASCADE, null=True, blank=True)
    proposed_content = models.TextField(blank=True)
    justification = models.TextField(blank=True)
    proposed_tags = models.TextField(blank=True, help_text="Önerilen etiketler (virgülle ayrılmış ID'ler)")
    draft_title = models.CharField(max_length=200, blank=True)  # Kullanıcının taslağa verdiği isim
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_proposal_type_display()} Taslağı"


class ArticleTag(models.Model):
    """Madde Etiketi/Kategorisi"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#3B82F6', help_text="Hex renk kodu (örn: #3B82F6)")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class DoctrineArticle(models.Model):
    """Doktrin Maddesi"""
    ARTICLE_TYPE_CHOICES = [
        ('FOUNDATION_LAW', 'İlke'),
        ('NORMAL_LAW', 'Yasa'),
    ]

    article_number = models.IntegerField()
    article_type = models.CharField(max_length=20, choices=ARTICLE_TYPE_CHOICES)
    content = models.TextField()
    justification = models.TextField(blank=True, null=True, help_text="Gerekçelendirme")
    tags = models.ManyToManyField(ArticleTag, blank=True, related_name='articles')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_articles')
    created_date = models.DateTimeField(auto_now_add=True)
    last_modified_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('article_type', 'article_number')
        ordering = ['article_type', 'article_number']
    
    def __str__(self):
        return f"{self.get_article_type_display()} {self.article_number}"


class ArticleVersion(models.Model):
    """Madde Versiyonu - Değişiklik Geçmişi"""
    article = models.ForeignKey(DoctrineArticle, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField(help_text="Versiyon numarası (1, 2, 3...)")
    content = models.TextField(help_text="Bu versiyondaki madde içeriği")
    justification = models.TextField(blank=True, null=True)
    changed_by_proposal = models.ForeignKey('Proposal', on_delete=models.SET_NULL, null=True, blank=True, related_name='article_versions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version_number']
        unique_together = ('article', 'version_number')

    def __str__(self):
        return f"{self.article} - v{self.version_number}"


class Proposal(models.Model):
    """Öneri - Değişiklik/Ekleme/İsim Değişikliği"""
    PROPOSAL_TYPE_CHOICES = [
        ('ADD', 'Madde Ekleme'),
        ('MODIFY', 'Madde Değişikliği'),
        ('REMOVE', 'Madde Kaldırma'),
        ('FOUNDER_REVISION', 'Kurucu Genel Düzenleme'),
        ('NAME_CHANGE', 'İsim Değişikliği'),
    ]
    
    PROPOSER_LEVEL_CHOICES = [
        ('SQUAD', 'Takım'),
        ('UNION', 'Birlik'),
        ('PROVINCE_ORG', 'İl Örgütü'),
        ('FOUNDER', 'Kurucu'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Aktif'),
        ('PASSED', 'Kabul Edildi'),
        ('REJECTED', 'Reddedildi'),
        ('ARCHIVED', 'Arşivlendi'),
    ]
    
    proposal_type = models.CharField(max_length=20, choices=PROPOSAL_TYPE_CHOICES)
    related_article = models.ForeignKey(DoctrineArticle, on_delete=models.SET_NULL, null=True, blank=True, related_name='proposals')
    original_article_content = models.TextField(blank=True, null=True, help_text="Değişiklik önerisi için: Maddenin değişiklikten önceki hali")
    proposed_content = models.TextField()
    justification = models.TextField(blank=True, null=True, help_text="Önerinin gerekçesi")
    proposed_by_level = models.CharField(max_length=20, choices=PROPOSER_LEVEL_CHOICES)
    proposed_by_entity_id = models.IntegerField()  # Team/Squad/Union/ProvinceOrg ID
    proposed_tags = models.TextField(blank=True, null=True, help_text="Önerilen etiketler (virgülle ayrılmış ID'ler)")
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')

    # Oy sayıları - cache için
    vote_yes_count = models.IntegerField(default=0)
    vote_abstain_count = models.IntegerField(default=0)
    vote_veto_count = models.IntegerField(default=0)
    
    def save(self, *args, **kwargs):
        if not self.end_date:
            # Oylama süresi: 14 gün
            from django.utils import timezone
            self.end_date = timezone.now() + timedelta(days=14)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_proposal_type_display()} - {self.status}"


class Vote(models.Model):
    """Oy"""
    VOTE_CHOICES = [
        ('YES', 'Kabul'),
        ('ABSTAIN', 'Çekimser'),
        ('VETO', 'Veto'),
    ]

    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='votes')
    vote_choice = models.CharField(max_length=10, choices=VOTE_CHOICES)
    voted_at = models.DateTimeField(auto_now=True)
    last_changed_at = models.DateTimeField(auto_now_add=True, null=True)  # İlk oy veya son değişiklik zamanı

    class Meta:
        unique_together = ('proposal', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.vote_choice}"

    def can_change_vote(self):
        """Kullanıcı oyunu değiştirebilir mi? (24 saat kontrolü)"""
        from django.utils import timezone
        from datetime import timedelta

        # Eğer last_changed_at boşsa (eski kayıtlar), değiştirilebilir
        if not self.last_changed_at:
            return True

        time_since_last_change = timezone.now() - self.last_changed_at
        return time_since_last_change >= timedelta(hours=24)


class Discussion(models.Model):
    """Tartışma/Yorum"""
    article = models.ForeignKey(DoctrineArticle, on_delete=models.CASCADE, null=True, blank=True, related_name='discussions')
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, null=True, blank=True, related_name='discussions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='discussions')
    comment_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)

    class Meta:
        ordering = ['-upvotes', 'created_at']  # En çok oy alan üstte

    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d')}"

    @property
    def score(self):
        """Net oy skoru"""
        return self.upvotes - self.downvotes


class DiscussionVote(models.Model):
    """Yorum Oylama - Upvote/Downvote"""
    VOTE_CHOICES = [
        ('UP', 'Upvote'),
        ('DOWN', 'Downvote'),
    ]

    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='discussion_votes')
    vote_type = models.CharField(max_length=4, choices=VOTE_CHOICES)
    voted_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('discussion', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.vote_type} - {self.discussion.id}"


class ArchivedProposal(models.Model):
    """Arşivlenmiş Öneri"""
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='archives')
    article = models.ForeignKey(DoctrineArticle, on_delete=models.SET_NULL, null=True, related_name='archives')
    archived_discussions = models.JSONField()  # Tartışmaların snapshot'ı
    final_vote_result = models.JSONField()  # Son oy sonuçları
    archived_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Arşiv - {self.proposal} - {self.archived_at.strftime('%Y-%m-%d')}"


class Reference(models.Model):
    """Kaynakça/Referans - Akademik kaynak ekleme sistemi"""
    REFERENCE_TYPE_CHOICES = [
        ('BOOK', 'Kitap'),
        ('ARTICLE', 'Makale'),
        ('JOURNAL', 'Dergi'),
        ('WEBSITE', 'Web Sitesi'),
        ('REPORT', 'Rapor'),
        ('THESIS', 'Tez'),
        ('OTHER', 'Diğer'),
    ]

    # Kim ekledi
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='references')

    # Kaynak bilgileri
    reference_type = models.CharField(max_length=20, choices=REFERENCE_TYPE_CHOICES, default='BOOK')
    author = models.CharField(max_length=500, help_text="Yazar(lar) - Örn: Kant, Immanuel veya Smith, J. & Doe, A.")
    title = models.CharField(max_length=500, help_text="Eser başlığı")
    year = models.IntegerField(help_text="Yayın yılı")
    publisher = models.CharField(max_length=300, blank=True, help_text="Yayınevi")
    city = models.CharField(max_length=100, blank=True, help_text="Yayın yeri")
    url = models.URLField(blank=True, help_text="Online kaynak linki")
    doi = models.CharField(max_length=100, blank=True, help_text="DOI numarası")
    isbn = models.CharField(max_length=50, blank=True, help_text="ISBN numarası")
    pages = models.CharField(max_length=50, blank=True, help_text="Sayfa aralığı - Örn: 157-189")

    # Ek bilgiler
    notes = models.TextField(blank=True, help_text="Notlar, açıklamalar")

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False, help_text="Kaynağın doğruluğu onaylandı mı?")

    class Meta:
        ordering = ['author', 'year']
        verbose_name = 'Referans'
        verbose_name_plural = 'Referanslar'

    def __str__(self):
        return f"{self.author} ({self.year}). {self.title}"

    def get_citation_short(self):
        """Kısa alıntı formatı: (Kant, 1789)"""
        # Yazar soyadı al (ilk kelime genelde soyadı)
        author_last = self.author.split(',')[0] if ',' in self.author else self.author.split()[0]
        return f"({author_last}, {self.year})"

    def get_citation_full(self):
        """Tam bibliyografik format"""
        citation = f"{self.author} ({self.year}). {self.title}."
        if self.publisher:
            citation += f" {self.publisher}."
        if self.city:
            citation += f" {self.city}."
        if self.url:
            citation += f" {self.url}"
        return citation


class ProposalReference(models.Model):
    """Öneri-Referans ilişkisi - Hangi öneri hangi kaynakları kullanıyor"""
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='references')
    reference = models.ForeignKey(Reference, on_delete=models.CASCADE, related_name='proposal_usages')
    page_number = models.CharField(max_length=50, blank=True, help_text="Atıfta kullanılan sayfa numarası - Örn: s.157")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('proposal', 'reference')
        ordering = ['added_at']

    def __str__(self):
        return f"{self.proposal.id} -> {self.reference.author} ({self.reference.year})"

    def get_inline_citation(self):
        """Metin içi alıntı: (Kant, 1789, s.157)"""
        author_last = self.reference.author.split(',')[0] if ',' in self.reference.author else self.reference.author.split()[0]
        citation = f"({author_last}, {self.reference.year}"
        if self.page_number:
            citation += f", {self.page_number}"
        citation += ")"
        return citation


class ArticleReference(models.Model):
    """Madde-Referans ilişkisi - Hangi madde hangi kaynakları kullanıyor"""
    article = models.ForeignKey(DoctrineArticle, on_delete=models.CASCADE, related_name='references')
    reference = models.ForeignKey(Reference, on_delete=models.CASCADE, related_name='article_usages')
    page_number = models.CharField(max_length=50, blank=True, help_text="Atıfta kullanılan sayfa numarası")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('article', 'reference')
        ordering = ['added_at']

    def __str__(self):
        return f"{self.article.article_number} -> {self.reference.author} ({self.reference.year})"

    def get_inline_citation(self):
        """Metin içi alıntı: (Kant, 1789, s.157)"""
        author_last = self.reference.author.split(',')[0] if ',' in self.reference.author else self.reference.author.split()[0]
        citation = f"({author_last}, {self.reference.year}"
        if self.page_number:
            citation += f", {self.page_number}"
        citation += ")"
        return citation