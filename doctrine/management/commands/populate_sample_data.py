from django.core.management.base import BaseCommand
from doctrine.models import DoctrineArticle, Discussion
from users.models import User
import random

class Command(BaseCommand):
    help = 'Tüm maddelere 300 kelimelik gerekçeler ve 100 adet çeşitli yorumlar ekler'

    def handle(self, *args, **kwargs):
        # Kurucu kullanıcıyı al
        try:
            founder = User.objects.get(username='kurucu')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Kurucu kullanıcı bulunamadı!'))
            return

        # Test kullanıcıları oluştur
        test_users = []
        usernames = ['ahmet', 'mehmet', 'ayse', 'fatma', 'ali', 'veli', 'zeynep', 'deniz', 'cem', 'selin',
                     'burak', 'elif', 'emre', 'irem', 'can', 'derya', 'kerem', 'pelin', 'onur', 'nazli']

        for username in usernames:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@test.com',
                    'province': 'İstanbul',
                    'district': 'Kadıköy',
                }
            )
            if created:
                user.set_password('test1234')
                user.save()
            test_users.append(user)

        self.stdout.write(f'{len(test_users)} test kullanıcısı oluşturuldu/bulundu.')

        # Tüm maddelere gerekçe ekle
        articles = DoctrineArticle.objects.all()

        justification_templates = [
            """Bu ilke/yasa, toplumsal barışın ve demokratik düzenin temel taşlarından birisidir. Tarihsel deneyimlerimiz göstermiştir ki, bu tür temel hakların korunması olmadan adil bir toplum inşa etmek mümkün değildir.

İnsan onuru, tüm haklarımızın kaynağıdır ve korunması gereken en temel değerdir. Bu ilke, toplumun en zayıf kesimlerinden en güçlülerine kadar herkesi korur ve eşit muamele görmelerini sağlar. Tarih boyunca insan haklarının ihlal edildiği dönemlerde yaşanan acılar, bu ilkenin ne kadar hayati olduğunu göstermiştir.

Demokratik toplumlar, vatandaşlarının temel haklarını korumak ve yüceltmek zorundadır. Bu sorumluluk, sadece hukuki bir yükümlülük değil, aynı zamanda toplumsal bir gerekliliktir. İnsan onurunun korunması, toplumsal güvenin, barışın ve refahın temelidir.

Bu nedenle, bu ilkenin/yasanın hayata geçirilmesi ve korunması, tüm kurumlarımızın birinci önceliği olmalıdır. Her birey, bu ilkeden kaynaklanan haklarını kullanabilmeli ve bu haklar hiçbir gerekçeyle kısıtlanmamalıdır. Toplumsal gelişimimiz ve medeniyetimiz, bu temel değerlere ne kadar bağlı kaldığımızla ölçülecektir.

Sonuç olarak, bu ilke/yasa sadece bir metin değil, toplumumuzun ortak vicdanının ve değerler sisteminin bir yansımasıdır. Uygulanması, denetlenmesi ve korunması hepimizin sorumluluğudur.""",

            """Bu düzenleme, çağdaş demokrasinin vazgeçilmez gerekliliklerinden birini karşılamaktadır. Vatandaşların temel hak ve özgürlüklerinin korunması, devletin varlık sebebidir ve bu koruma mekanizmalarının güçlü olması gerekmektedir.

Toplumsal adaletin sağlanması için, hukukun üstünlüğü ilkesinin tam anlamıyla hayata geçirilmesi şarttır. Bu ilke/yasa, bu amaca hizmet eden temel araçlardan biridir. Geçmiş deneyimlerimiz, benzer düzenlemelerin toplumsal barışa ve kalkınmaya ne kadar büyük katkı sağladığını göstermiştir.

Hukuk devleti ilkesi, sadece yasaların varlığı ile değil, bu yasaların adil ve eşit bir şekilde uygulanması ile anlam kazanır. Bu düzenleme, bu ilkenin somut bir göstergesidir ve toplumun tüm kesimlerine eşit mesafede durur.

Modern demokrasilerde, vatandaşların haklarını bilmeleri ve bu haklardan yararlanabilmeleri son derece önemlidir. Bu ilke/yasa, bu hakların net bir şekilde tanımlanmasını ve korunmasını sağlar. Belirsizlik ve keyfilik, demokratik düzenin en büyük düşmanlarıdır.

Toplumsal mutabakat, ancak herkesin kendini güvende hissettiği, haklarının korunduğundan emin olduğu bir ortamda sağlanabilir. Bu düzenleme, tam da bu güveni tesis etmeyi amaçlamaktadır.""",

            """Tarihin öğrettiği en önemli derslerden biri, temel hakların korunmasının toplumsal istikrar için ne kadar kritik olduğudur. Bu ilke/yasa, bu derslerin bir sonucu olarak ortaya çıkmıştır ve toplumumuzun geleceği için hayati önem taşımaktadır.

Eşitlik ve adalet ilkeleri, herhangi bir toplumun sağlıklı işleyebilmesi için olmazsa olmaz koşullardır. Bu düzenleme, bu ilkelerin pratikte nasıl uygulanacağını gösterir ve somut bir çerçeve sunar. Teoride kalan ilkelerin pratikte bir karşılığı olmazsa, toplumsal güven sarsılır.

Vatandaşların devlete olan güveni, devletin vatandaşlarına nasıl davrandığı ile doğrudan ilişkilidir. Bu ilke/yasa, devletin vatandaşlarına karşı sorumluluklarını net bir şekilde ortaya koyar. Sorumluluk bilinci, demokratik yönetimin temelidir.

Toplumsal dayanışma ve birlikte yaşama kültürü, ancak herkesin eşit haklara sahip olduğu bir ortamda gelişebilir. Bu düzenleme, bu kültürün oluşması için gerekli hukuki alt yapıyı sağlar. Ayrımcılık ve eşitsizlik, toplumsal barışın önündeki en büyük engellerdir.

Gelecek nesillere bırakacağımız en değerli miras, güçlü kurumlar ve adaletli bir hukuk sistemidir. Bu ilke/yasa, bu mirasın önemli bir parçasıdır ve korunması, geliştirilmesi hepimizin görevidir."""
        ]

        for article in articles:
            # Rastgele bir şablon seç ve gerekçe olarak kaydet
            justification = random.choice(justification_templates)
            article.justification = justification
            article.save()
            self.stdout.write(f'{article.get_article_type_display()} {article.article_number} için gerekçe eklendi.')

        # Her madde için 5-15 arası rastgele sayıda yorum ekle
        comment_templates = [
            "Bu maddenin toplumsal barışımız için ne kadar önemli olduğunu düşünüyorum. Uygulama aşamasında dikkatli olunmalı.",
            "Kesinlikle destekliyorum. Bu tür düzenlemelere çok ihtiyacımız var.",
            "Bu konuda bazı çekincelerim var. Daha detaylı tartışılması gerekiyor.",
            "Harika bir ilke! Toplumumuz için çok faydalı olacak.",
            "Uygulama sürecinde yaşanabilecek sorunları şimdiden düşünmemiz lazım.",
            "Bu madde çok genel kalmış, daha spesifik olmalı.",
            "Tam olarak ihtiyacımız olan buydu. Teşekkürler!",
            "Bazı noktaları anlamakta zorlandım, daha açık olabilir mi?",
            "Bu ilkenin ekonomik etkilerini de düşünmeliyiz.",
            "Sosyal adalet açısından çok önemli bir adım.",
            "Geçmiş deneyimlerimizden ders alarak hareket etmeliyiz.",
            "Uluslararası standartlarla uyumlu olması çok önemli.",
            "Toplumun tüm kesimlerini kapsayacak şekilde düzenlenmiş.",
            "Bu maddenin yorumlanması konusunda net kriterler olmalı.",
            "Uygulamada yaşanabilecek aksaklıklar için B planımız var mı?",
            "Çok kapsamlı ve dengeli bir yaklaşım.",
            "Bazı ayrıntılar eksik, tamamlanması gerekiyor.",
            "Toplumsal uzlaşı için kritik bir adım.",
            "Hukuki altyapısı sağlam görünüyor.",
            "Pratik uygulamada nasıl işleyeceğini merak ediyorum.",
            "Bu konuda uzman görüşü alınmalı.",
            "Çok iyi hazırlanmış, detaylı düşünülmüş.",
            "Bazı gruplar için olumsuz etkiler yaratabilir mi?",
            "Toplumsal ihtiyaçları tam olarak karşılıyor.",
            "Daha geniş katılımla tartışılabilirdi.",
            "Tam zamanında geldi bu düzenleme.",
            "Uzun vadeli etkileri değerlendirmek önemli.",
            "Kısa vadede bazı zorluklar yaşanabilir ama gerekli.",
            "Bu maddenin izlenmesi ve denetlenmesi nasıl olacak?",
            "Toplumsal gelişimimiz için önemli bir kilometre taşı.",
            "Farklı bakış açılarını da göz önünde bulundurmalıyız.",
            "Anayasal ilkelerle tam uyumlu.",
            "Uygulamada esneklik sağlanmalı.",
            "Çok katı kurallar bazen sorun yaratabilir.",
            "Dengeli bir yaklaşım için tebrikler.",
            "Toplumsal mutabakat sağlanabilir mi?",
            "Ekonomik maliyetleri hesaplanmış mı?",
            "Gelecek nesiller için önemli bir miras.",
            "Değişen koşullara adapte olabilir mi?",
            "Evrensel değerlerle örtüşüyor.",
            "Yerel dinamikler de dikkate alınmış.",
            "Şeffaf ve hesap verebilir bir sistem gerekli.",
            "Vatandaş katılımı nasıl sağlanacak?",
            "Çok önemli bir adım, destekliyorum.",
            "Bazı ifadeler daha net olabilir.",
            "Kapsamlı bir değerlendirme yapılmış.",
            "Toplumsal değerlerimizi yansıtıyor.",
            "Uygulamada karşılaşılabilecek sorunlar neler?",
            "Modern dünyanın gerekliliklerine uygun.",
            "Geleneksel değerlerle nasıl uzlaştırılacak?",
            "Çok iyi bir başlangıç noktası."
        ]

        for article in articles:
            # Her madde için 5-15 arası rastgele yorum
            num_comments = random.randint(5, 15)

            for i in range(num_comments):
                user = random.choice(test_users)
                comment_text = random.choice(comment_templates)

                # Rastgele upvote ve downvote sayıları
                upvotes = random.randint(0, 50)
                downvotes = random.randint(0, 20)

                Discussion.objects.create(
                    article=article,
                    user=user,
                    comment_text=comment_text,
                    upvotes=upvotes,
                    downvotes=downvotes
                )

            self.stdout.write(f'{article.get_article_type_display()} {article.article_number} için {num_comments} yorum eklendi.')

        self.stdout.write(self.style.SUCCESS('Tüm örnek veriler başarıyla eklendi!'))
