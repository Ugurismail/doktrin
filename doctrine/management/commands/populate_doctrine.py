from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from doctrine.models import DoctrineArticle

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate doctrine with 50 foundation principles and 200 laws'

    def handle(self, *args, **options):
        # Kurucu kullanıcıyı bul veya oluştur
        founder, created = User.objects.get_or_create(
            username='kurucu',
            defaults={
                'email': 'kurucu@doktrin.org',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            founder.set_password('kurucu123')
            founder.save()
            self.stdout.write(self.style.SUCCESS('Kurucu kullanıcı oluşturuldu'))

        # Kuruluş İlkeleri (50 madde)
        foundation_principles = [
            # I. Temel İlkeler (1-10)
            {
                'content': "İnsan onuru dokunulmazdır. Devletin tüm kurumları ve politikaları, insan onurunu korumak ve yüceltmek zorundadır.",
                'justification': "İnsan onuru, tüm haklarin ve özgürlüklerin kaynağıdır. Bir toplumun medeniyeti, bireylerine gösterdiği saygıyla ölçülür. Devlet, vatandaşlarının onurunu korumak için vardır; bu temel ilke olmadan adalet, eşitlik ve özgürlük anlamsız kalır. İnsan onurunun korunması, toplumsal barışın ve demokratik düzenin vazgeçilmez temelidir."
            },
            {
                'content': "Eşitlik ve adalet toplumun temel direğidir. Hiç kimse ırk, cinsiyet, din, dil, etnik köken veya sosyal statüsü nedeniyle ayrımcılığa uğrayamaz.",
                'justification': "Toplumsal eşitlik, demokratik bir düzenin ön koşuludur. Ayrımcılık, toplumsal huzursuzluğun ve adaletsizliğin temel kaynağıdır. Her bireyin eşit fırsatlara sahip olması, toplumsal dayanışmayı güçlendirir ve ekonomik kalkınmayı destekler. Eşitlik ilkesi olmadan, özgürlük ve adalet yalnızca ayrıcalıklı azınlıklar için geçerli olur."
            },
            {
                'content': "Özgürlük, sorumluluğun karşılığıdır. Her birey, başkalarının haklarını ihlal etmediği sürece düşünce, ifade ve eylem özgürlüğüne sahiptir.",
                'justification': "Özgürlük, insanın doğasında vardır ve demokratik toplumun temel taşıdır. Ancak özgürlük, başkalarının haklarını ihlal etme lisansı değildir. Sorumlu özgürlük anlayışı, bireysel haklar ile toplumsal düzen arasında denge kurar. Bu ilke, hem bireysel gelişimi hem de toplumsal uyumu mümkün kılar."
            },
            {
                'content': "Bilgi ve eğitim herkese açık kamusal bir haktır. Eğitim sistemi, eleştirel düşünmeyi teşvik eden, bilimsel ve laik temellere dayalı olmalıdır.",
                'justification': "Eğitim, toplumsal eşitsizliği azaltan en güçlü araçtır. Bilgiye erişim, bireylerin özgür ve bilinçli kararlar almasını sağlar. Eleştirel düşünme ve bilimsel yöntem, dogmatizme ve manipülasyona karşı en önemli korumadır. Nitelikli ve eşit eğitim, demokratik katılımın ve ekonomik kalkınmanın temelidir."
            },
            {
                'content': "Ekonomik adalet, toplumsal barışın temelidir. Servet dağılımı adaletli olmalı, hiç kimse açlık ve yoksulluk içinde yaşamamalıdır.",
                'justification': "Ekonomik adaletsizlik, sosyal huzursuzluğun ve çatışmaların ana kaynağıdır. Aşırı servet eşitsizliği, demokrasiyi zayıflatır ve oligarşik yapılar oluşturur. Her insanın insanca yaşamak için gerekli kaynaklara erişimi, temel bir haktır. Adil servet dağılımı, ekonomik büyümeyi sürdürülebilir kılar ve toplumsal dayanışmayı güçlendirir."
            },
            {
                'content': "Doğa ve çevre, gelecek nesillere emanettir. Sürdürülebilir kalkınma, tüm ekonomik ve sosyal politikaların merkezinde olmalıdır.",
                'justification': "İklim krizi ve ekolojik tahribat, insanlığın karşılaştığı en büyük tehdittir. Bugünkü neslin refahı, gelecek nesillerin haklarını yok etme pahasına sağlanamaz. Sürdürülebilir kalkınma, ekonomik büyüme ile ekolojik denge arasında uzlaşma sağlar. Çevreyi korumak, hem ahlaki bir sorumluluk hem de ekonomik bir zorunluluktur."
            },
            {
                'content': "Demokrasi, yalnızca oy kullanmak değildir. Katılımcı demokrasi, şeffaflık ve hesap verebilirlik tüm yönetim kademelerinde uygulanmalıdır.",
                'justification': "Gerçek demokrasi, vatandaşların yalnızca seçimlerde değil, karar alma süreçlerinin her aşamasında aktif rol almasını gerektirir. Şeffaflık, yolsuzluğu önler ve halkın güvenini kazanır. Hesap verebilirlik, iktidarın keyfi kullanımını engeller. Katılımcı demokrasi, politikaların halkın gerçek ihtiyaçlarını karşılamasını sağlar."
            },
            {
                'content': "Hukukun üstünlüğü tartışılmazdır. Hiç kimse, hiçbir kurum yasaların üstünde değildir. Yargı bağımsızlığı mutlak olarak korunmalıdır.",
                'justification': "Hukukun üstünlüğü olmadan, demokrasi ve özgürlük savunmasız kalır. Güçlülerin keyfi iradesi yerine, herkes için geçerli olan kurallar toplumsal düzenin temelidir. Bağımsız yargı, iktidarın dengelenmesini ve bireylerin haklarının korunmasını sağlar. Hukuk devleti, adaleti ve eşitliği garanti eder."
            },
            {
                'content': "Barış, çatışmadan üstündür. Uluslararası ilişkilerde diyalog ve işbirliği önceliklidir, savaş son çare olmalıdır.",
                'justification': "Savaş, insanlık için en büyük trajedilerden biridir ve nesiller boyu süren acılara neden olur. Diplomasi ve diyalog, sorunları çözmenin en akılcı ve insani yoludur. Barış, ekonomik kalkınmanın ve sosyal refahın ön koşuludur. Uluslararası işbirliği, küresel sorunlara karşı en etkili yanıttır."
            },
            {
                'content': "Bilim ve akıl, karar alma süreçlerinin temelidir. Politikalar, kanıta dayalı ve bilimsel araştırmalarla desteklenmelidir.",
                'justification': "Bilimsel yöntem, dogma ve önyargıya karşı en güçlü korumadır. Kanıta dayalı politikalar, kaynakların verimli kullanılmasını ve etkili sonuçlar alınmasını sağlar. Akıl ve bilim, toplumun karşılaştığı karmaşık sorunlara rasyonel çözümler üretir. Bilimsel düşünce, ilerlemenin ve refahın temel kaynağıdır."
            },

            # II. Ekonomik Haklar (11-20)
            {
                'content': "Çalışma, hem bir hak hem de bir onurdur. Her birey, insanca yaşamaya yeterli, adil bir ücret alma hakkına sahiptir.",
                'justification': "Çalışma, insanın kendini gerçekleştirmesinin ve topluma katkıda bulunmasının temel yoludur. Adil ücret, insan onurunun ve ekonomik bağımsızlığın gereğidir. Sömürü koşullarında çalışmak, kölelikten farksızdır. İnsanca bir yaşam standardı, tüm çalışanlar için garanti edilmelidir."
            },
            {
                'content': "Sendikal örgütlenme özgürlüğü korunmalıdır. İşçiler, haklarını savunmak için örgütlenebilir ve toplu pazarlık yapabilirler.",
                'justification': "İşçiler ile işverenler arasındaki güç dengesizliği, örgütlenme hakkı olmadan işçileri savunmasız bırakır. Sendikalar, adil ücret ve çalışma koşulları için en etkili araçtır. Toplu pazarlık, demokratik bir haktır ve sosyal barışı güçlendirir. Örgütlü işçiler, ekonomik demokrasinin temel aktörleridir."
            },
            {
                'content': "Sosyal güvenlik evrensel bir haktır. Sağlık hizmetleri, emeklilik ve işsizlik sigortası herkes için erişilebilir olmalıdır.",
                'justification': "Sosyal güvenlik, bireyleri yaşamın belirsizliklerine karşı korur ve onurlu bir yaşam sağlar. Evrensel sosyal güvenlik, toplumsal dayanışmanın somut ifadesidir. Hastalık, yaşlılık veya işsizlik nedeniyle yoksulluğa düşmek, kabul edilemez. Güçlü sosyal güvenlik sistemi, ekonomik istikrarı da destekler."
            },
            {
                'content': "Toprak ve doğal kaynaklar, milletin ortak varlığıdır. Kullanımı adaletli olmalı ve toplum yararına düzenlenmelidir.",
                'justification': "Doğal kaynaklar, doğada hazır bulunur ve birkaç kişinin tekelinde olamaz. Bu kaynakların özel çıkarlar için sömürülmesi, toplumsal adaletsizliğe yol açar. Toprak ve kaynaklar, tüm toplumun refahına hizmet etmelidir. Kamusal kontrol, sürdürülebilir ve adil kullanımı garanti eder."
            },
            {
                'content': "Kooperatifler ve dayanışma ekonomisi desteklenmelidir. Ekonomik demokrasi, işçilerin üretime ve yönetime katılımını gerektirir.",
                'justification': "Kooperatifler, ekonomik demokrasinin ve işçi özgürleşmesinin araçlarıdır. Üretim araçlarının toplumsal mülkiyeti, sömürüyü ortadan kaldırır. İşçilerin yönetime katılımı, verimliliği artırır ve adaleti sağlar. Dayanışma ekonomisi, rekabetçi kapitalizme insani bir alternatiftir."
            },
            {
                'content': "Gelir eşitsizliği sistematik olarak azaltılmalıdır. Vergi sistemi, zenginlikten fakire kaynak transferini sağlayacak şekilde yapılandırılmalıdır.",
                'justification': "Aşırı gelir eşitsizliği, sosyal uyumu bozar ve demokratik kurumları zayıflatır. Adil vergi sistemi, zenginliğin topluma yeniden dağıtılmasını sağlar. Fakir kesimler üzerindeki vergi yükü, adaletsizliği derinleştirir. Progresif vergileme, ekonomik adaleti ve toplumsal barışı destekler."
            },
            {
                'content': "Finans sistemi reel ekonomiye hizmet etmelidir. Spekülasyon ve rant ekonomisi yerine üretken yatırımlar teşvik edilmelidir.",
                'justification': "Finans sektörünün aşırı büyümesi, ekonomik krizlere ve istikrarsızlığa yol açar. Spekülasyon, toplumsal zenginlik yaratmaz, yalnızca yeniden dağıtır. Üretken yatırımlar, istihdam ve ekonomik büyümeyi destekler. Finans sistemi, gerçek ekonomik faaliyetleri desteklemek için düzenlenmelidir."
            },
            {
                'content': "Kamu hizmetleri özelleştirilemez. Su, enerji, ulaşım gibi temel hizmetler kamu kontrolünde ve kâr amacı gütmeden sunulmalıdır.",
                'justification': "Temel hizmetler, herkes için erişilebilir olmalıdır, zenginlik düzeyine göre değişmemelidir. Özelleştirme, fiyatları artırır ve hizmet kalitesini düşürür. Kamu hizmetleri, toplumsal dayanışmanın ve eşitliğin ifadesidir. Kâr amacı gütmeyen kamu hizmeti, evrensel erişimi garanti eder."
            },
            {
                'content': "Gıda egemenliği savunulmalıdır. Tarımsal üretim, küçük üreticileri destekleyen ve yerel gıda sistemlerini güçlendiren şekilde düzenlenmelidir.",
                'justification': "Gıda güvenliği, ulusal güvenliğin temel unsurudur. Küçük çiftçiler, sürdürülebilir tarımın ve kırsal kalkınmanın omurgasıdır. Endüstriyel tarım, çevreye zarar verir ve yerel toplulukları zayıflatır. Gıda egemenliği, toplumların kendi tarım politikalarını belirleme hakkıdır."
            },
            {
                'content': "Borçlanma sorumlu ve sürdürülebilir olmalıdır. Kamu borçları, gelecek nesilleri yoksullaştıracak şekilde artırılamaz.",
                'justification': "Aşırı borçlanma, gelecek nesillerin kaynaklarını bugün tüketmek anlamına gelir. Borç yükü, kamu hizmetlerini kısıtlar ve sosyal harcamaları azaltır. Sürdürülebilir mali politika, nesiller arası adaleti gerektirir. Sorumlu borçlanma, ekonomik istikrarı ve uzun vadeli refahı destekler."
            },

            # III. Sosyal ve Kültürel Haklar (21-30)
            {
                'content': "Sağlık hizmeti, herkes için ücretsiz ve eşit erişilebilir olmalıdır. Sağlık bir ticaret konusu değil, temel bir haktır.",
                'justification': "Sağlık, yaşam hakkının temel bileşenidir ve parayla ölçülemez. Sağlık hizmetlerinin ticarileşmesi, yoksulları ölüme terk etmek anlamına gelir. Evrensel sağlık hizmeti, toplumsal eşitliğin ve dayanışmanın ifadesidir. Sağlıklı bir toplum, ekonomik kalkınmanın da ön koşuludur."
            },
            {
                'content': "Barınma hakkı korunmalıdır. Herkes, güvenli ve sağlıklı bir konut hakkına sahiptir, konut spekülasyonu önlenmelidir.",
                'justification': "Barınma, insan onurunun ve aile yaşamının temelidir. Konut, spekülasyon aracı değil, temel bir ihtiyaçtır. Evsizlik, toplumsal bir başarısızlıktır ve önlenebilir. Barınma hakkının korunması, sosyal istikrarı ve halk sağlığını destekler."
            },
            {
                'content': "Kültürel çeşitlilik zenginliktir. Tüm dil, kültür ve inanç grupları eşit saygı görmelidir.",
                'justification': "Kültürel çeşitlilik, toplumun zenginliğini ve yaratıcılığını artırır. Tek tip kültürel dayatma, bireysel özgürlüğü ve toplumsal dinamizmi yok eder. Farklı kültürlerin bir arada yaşaması, hoşgörü ve demokratik kültürü geliştirir. Kültürel hakların tanınması, azınlık gruplarının topluma katılımını güçlendirir."
            },
            {
                'content': "Sanat ve bilim özgürdür. Sanatsal ve bilimsel ifade, sansür ve baskıdan korunmalıdır.",
                'justification': "Sanat ve bilim, toplumsal ilerlemenin ve eleştirel düşüncenin kaynaklarıdır. Sansür, yaratıcılığı öldürür ve toplumu geriye götürür. Özgür düşünce ortamı, yenilikçiliği ve kültürel gelişimi destekler. Sanat ve bilim özgürlüğü, demokratik toplumun vazgeçilmez unsurudur."
            },
            {
                'content': "Medya çoğulculuğu ve bağımsızlığı korunmalıdır. Haber ve bilgi erişimi, tekelleşmeye karşı korunmalıdır.",
                'justification': "Bağımsız medya, demokrasinin bekçisidir ve iktidarı denetler. Medya tekelleşmesi, enformasyon çeşitliliğini yok eder ve manipülasyona yol açar. Çok seslilik, vatandaşların bilinçli karar almasını sağlar. Özgür basın, yolsuzluğu ve hak ihlallerini ortaya çıkarır."
            },
            {
                'content': "Çocuklar toplumun geleceğidir. Çocuk haklarının korunması, kaliteli eğitim ve sağlık hizmetleri önceliklidir.",
                'justification': "Çocuklara yapılan yatırım, toplumun geleceğine yapılan yatırımdır. Çocuk haklarının ihlali, nesiller boyu süren travmalara neden olur. Kaliteli eğitim ve sağlık, her çocuğun potansiyelini gerçekleştirmesini sağlar. Çocukları korumak, medeni toplumun ahlaki yükümlülüğüdür."
            },
            {
                'content': "Toplumsal cinsiyet eşitliği sağlanmalıdır. Kadına yönelik şiddet ve ayrımcılık her türlü ile mücadele edilmelidir.",
                'justification': "Cinsiyet eşitliği, demokratik toplumun temel ilkesidir. Kadına yönelik şiddet, insan hakları ihlalidir ve toplumsal bir hastalıktır. Kadınların ekonomik ve politik katılımı, toplumsal kalkınmayı hızlandırır. Cinsiyet eşitliği olmadan, gerçek demokrasi ve adalet mümkün değildir."
            },
            {
                'content': "Yaşlıların onuru korunmalıdır. Yaşlı bakımı, sadece bir hizmet değil, nesiller arası dayanışmanın gereğidir.",
                'justification': "Yaşlılara gösterilen saygı, toplumun medeniyetinin göstergesidir. Yaşlılar, toplumun tecrübe ve bilgelik kaynağıdır. Onurlu yaşlanma hakkı, herkes için garanti edilmelidir. Nesiller arası dayanışma, toplumsal bağları güçlendirir ve kültürel aktarımı sağlar."
            },
            {
                'content': "Engelli bireyler için erişilebilirlik zorunludur. Toplum, tüm bireylerin eşit katılımını sağlayacak şekilde düzenlenmelidir.",
                'justification': "Engelli bireylerin toplumsal yaşama katılımı, eşitlik ilkesinin gereğidir. Erişilebilirlik, yalnızca fiziksel mekan değil, tüm hizmetleri kapsamalıdır. Engellilerin marjinalleşmesi, toplumsal kaynak kaybıdır. Kapsayıcı toplum tasarımı, herkesin hayat kalitesini artırır."
            },
            {
                'content': "Göç bir suç değildir. Göçmen ve mültecilerin hakları, insani değerlere uygun şekilde korunmalıdır.",
                'justification': "Göç, insanlık tarihinin doğal bir parçasıdır ve ekonomik dinamizmi artırır. Mültecilerin korunması, uluslararası hukuki yükümlülüktür ve insani bir sorumluluktur. Göçmenlerin ayrımcılığa uğraması, toplumsal uyumu bozar. İnsani değerler, sınırlardan daha önemlidir."
            },

            # IV. Politik Haklar ve Katılım (31-40)
            {
                'content': "Seçme ve seçilme hakkı evrenseldir. Her yetişkin vatandaş, demokratik sürece eşit şekilde katılabilmelidir.",
                'justification': "Seçme hakkı, demokrasinin temel taşıdır ve her yetişkin için garanti edilmelidir. Seçme hakkının kısıtlanması, demokratik meşruiyeti zedeler. Eşit siyasi katılım, hükümetlerin halkın iradesini yansıtmasını sağlar. Evrensel oy hakkı, siyasi eşitliğin ve toplumsal adaletin temelidir."
            },
            {
                'content': "Referandum ve halk girişimi mekanizmaları güçlendirilmelidir. Halk, önemli kararlarda doğrudan söz sahibi olmalıdır.",
                'justification': "Doğrudan demokrasi, temsili demokrasiyi güçlendirir ve halkın iradesini somutlaştırır. Referandum, kritik konularda halkın doğrudan karar vermesini sağlar. Halk girişimi, vatandaşların gündem belirleme gücünü artırır. Katılımcı demokrasi mekanizmaları, siyasi yabancılaşmayı azaltır."
            },
            {
                'content': "Yerel yönetimler güçlendirilmelidir. Yerinden yönetim ilkesi, karar alma süreçlerini halka yaklaştırır.",
                'justification': "Yerinden yönetim, demokrasiyi derinleştirir ve yerel ihtiyaçlara duyarlılığı artırır. Yerel sorunlar, yerelde yaşayanlar tarafından daha iyi anlaşılır ve çözülür. Güçlü yerel yönetimler, vatandaşların siyasete katılımını kolaylaştırır. Merkeziyetçilik, bürokratik verimsizliğe ve halktan kopukluğa yol açar."
            },
            {
                'content': "Sivil toplum desteklenmelidir. STK'lar, sendikalar ve halk örgütleri demokratik yaşamın vazgeçilmez unsurudur.",
                'justification': "Sivil toplum, devlet ile birey arasında köprü kurar ve demokratik kültürü geliştirir. STK'lar, toplumsal sorunlara çözüm üretir ve savunuculuk yapar. Örgütlü sivil toplum, iktidarı denetler ve hesap verebilirliği artırır. Güçlü sivil toplum, demokratik dayanıklılığın temelidir."
            },
            {
                'content': "Bilgi edinme hakkı korunmalıdır. Kamu kurumları şeffaf çalışmalı, vatandaşlar bilgiye kolayca erişebilmelidir.",
                'justification': "Bilgi edinme hakkı, demokratik katılımın ön koşuludur. Şeffaflık, yolsuzluğu önler ve kamu güvenini artırır. Gizlilik, yalnızca istisnai durumlarda meşrudur. Bilgiye erişim, vatandaşların bilinçli kararlar almasını ve iktidarı denetlemesini sağlar."
            },
            {
                'content': "Toplumsal muhalefet meşrudur. Barışçıl protesto ve gösteri hakkı, demokratik toplumun vazgeçilmez unsurudur.",
                'justification': "Muhalefet, demokrasinin hayati unsurudur ve iktidarın dengelenmesini sağlar. Protesto hakkı, sözünü duyuramayanların sesini yükseltir. Barışçıl gösteriler, toplumsal değişimin itici gücüdür. Muhalefeti susturan rejimler, otoriterleşir ve meşruiyetini kaybeder."
            },
            {
                'content': "Siyasi partiler, toplumun çoğulcu yapısını yansıtmalıdır. Parti içi demokrasi ve hesap verebilirlik zorunludur.",
                'justification': "Siyasi partiler, demokrasinin temel aktörleridir ve toplumsal çeşitliliği yansıtmalıdır. Parti içi demokrasi, nitelikli liderlerin yetişmesini sağlar. Hesap verebilirlik olmadan, partiler oligarşik yapılara dönüşür. Demokratik partiler, sağlıklı temsili demokrasinin temelidir."
            },
            {
                'content': "Kamu görevlileri halka hizmet eder. Rüşvet, yolsuzluk ve kayırmacılık en ağır şekilde cezalandırılmalıdır.",
                'justification': "Kamu görevlileri, toplumun emanetçileridir ve kamuya hizmet etmek zorundadır. Yolsuzluk, kamu kaynaklarını çalar ve adaleti tahrip eder. Rüşvet ve kayırmacılık, liyakat sistemini yıkar ve kamu güvenini sarsır. Etik kamu yönetimi, toplumsal refahın ve adaletin temelidir."
            },
            {
                'content': "Askeri yapı sivil denetime tabidir. Ordu, toplumdan kopuk bir güç olamaz, demokratik denetime açık olmalıdır.",
                'justification': "Sivil denetim, askeri darbeleri önler ve demokrasiyi korur. Ordu, halkın hizmetinde olmalıdır, halkın üzerinde değil. Denetim mekanizmaları olmadan, askeri güç demokratik kurumları tehdit eder. Sivil üstünlük, demokratik istikrarın garantisidir."
            },
            {
                'content': "Uluslararası dayanışma esastır. Halkların kendi kaderini tayin hakkı, emperyalizme ve sömürgeciliğe karşı savunulmalıdır.",
                'justification': "Halkların kaderini tayin hakkı, uluslararası hukukun temel ilkesidir. Emperyalizm ve sömürgecilik, adaletsizliğin ve sömürünün kaynaklarıdır. Uluslararası dayanışma, küresel adaleti ve barışı destekler. Tüm halklar, kendi geleceklerini özgürce belirleme hakkına sahiptir."
            },

            # V. Çevresel ve Gelecek Nesiller (41-50)
            {
                'content': "İklim krizi ile mücadele acildir. Karbon salımları hızla azaltılmalı, fosil yakıtlardan çıkış planlanmalıdır.",
                'justification': "İklim krizi, insanlığın karşılaştığı en büyük egzistansiyel tehdittir. Bilimsel veriler, acil eylemin gerekliliğini açıkça göstermektedir. Fosil yakıtların kullanımı, gelecek nesillerin yaşam hakkını tehdit eder. İklim adaleti, nesiller arası ve küresel eşitliğin gereğidir."
            },
            {
                'content': "Su kaynakları özelleştirilemez. Su, toplumun ortak malıdır ve gelecek nesiller için korunmalıdır.",
                'justification': "Su, yaşamın temel unsurudur ve ticarileştirilmesi kabul edilemez. Su kaynaklarının özelleştirilmesi, halk sağlığını tehdit eder ve eşitsizliği artırır. Gelecek nesillerin su güvenliği, bugünkü neslin sorumluluğudur. Evrensel su erişimi, temel bir insan hakkıdır."
            },
            {
                'content': "Biyoçeşitlilik korunmalıdır. Ekosistem tahribi ve türlerin yok oluşu önlenmelidir.",
                'justification': "Biyoçeşitlilik, ekosistemlerin sağlığının ve dayanıklılığının temelidir. Türlerin yok oluşu, ekolojik dengeyi bozar ve geri döndürülemez kayıplara neden olur. Ekosistem hizmetleri, insan yaşamını ve ekonomiyi destekler. Doğanın korunması, gelecek nesillere karşı ahlaki yükümlülüğümüzdür."
            },
            {
                'content': "Nükleer enerji reddedilir. Yenilenebilir ve sürdürülebilir enerji kaynakları teşvik edilmelidir.",
                'justification': "Nükleer enerji, çözülmemiş atık sorunları ve felaket riski nedeniyle kabul edilemez. Nükleer kazalar, nesiller boyu süren çevresel ve sağlık tahribatına neden olur. Yenilenebilir enerji, temiz ve sürdürülebilir alternatifler sunar. Enerji geçişi, iklim krizi ile mücadelenin temel unsurudur."
            },
            {
                'content': "Atık yönetimi döngüsel ekonomiye dayalı olmalıdır. Tek kullanımlık ürünler azaltılmalı, geri dönüşüm yaygınlaştırılmalıdır.",
                'justification': "Doğrusal ekonomi modeli, kaynakları tükenir ve çevreyi kirletir. Döngüsel ekonomi, atığı kaynak olarak değerlendirir ve sürdürülebilirliği artırır. Tek kullanımlık plastikler, okyanuslarda ve ekosistemlerde büyük tahribat yapar. Geri dönüşüm, kaynak verimliliğini ve çevre korumasını destekler."
            },
            {
                'content': "Şehirler, insan odaklı planlanmalıdır. Yeşil alanlar, toplu taşıma ve yaya ulaşımı önceliklendirilmelidir.",
                'justification': "İnsan odaklı şehir planlaması, yaşam kalitesini artırır ve toplumsal eşitliği destekler. Otomobil merkezli planlar, hava kirliliğine ve sosyal izolasyona yol açar. Yeşil alanlar, halk sağlığını ve ruh sağlığını iyileştirir. Sürdürülebilir ulaşım, iklim hedeflerine ulaşmanın anahtarıdır."
            },
            {
                'content': "Hayvan hakları korunmalıdır. Hayvanlara karşı kötü muamele yasaklanmalı, hayvan refah standartları yükseltilmelidir.",
                'justification': "Hayvanlar, acı çekebilen canlılardır ve ahlaki olarak korunmayı hak ederler. Hayvanlara kötü muamele, toplumsal şiddetin göstergesidir. Endüstriyel hayvancılık, hayvan acısına ve çevresel tahribata neden olur. Hayvan refahı, medeni toplumun ahlaki sorumluluğudur."
            },
            {
                'content': "Genetik mühendislik etik sınırlar içinde kalmalıdır. İnsan genomu ticarileştirilemez, genetik ayrımcılık yapılamaz.",
                'justification': "Genetik teknolojiler, büyük fırsatlar sunar ancak etik riskler taşır. İnsan genomunun ticarileşmesi, insan onurunu ihlal eder. Genetik ayrımcılık, yeni bir eşitsizlik kaynağı olabilir. Biyoteknoloji, sıkı etik ve yasal düzenlemelere tabi olmalıdır."
            },
            {
                'content': "Dijital haklar temel haklardandır. İnternet erişimi, mahremiyet ve dijital özgürlük korunmalıdır.",
                'justification': "Dijital teknolojiler, modern yaşamın temel unsurudur ve erişim eşitliği gerektirir. İnternet erişimi, eğitim, istihdam ve sosyal katılım için kritiktir. Dijital mahremiyet, gözetim toplumuna karşı korunmalıdır. Dijital haklar, demokratik katılımın ve ifade özgürlüğünün ön koşuludur."
            },
            {
                'content': "Gelecek nesillerin hakları bugünkü kararlarla korunmalıdır. Her politika, yedi nesil ilerisini düşünerek yapılmalıdır.",
                'justification': "Gelecek nesiller, bugünkü kararlarımızın sonuçlarını yaşayacaktır ve haklarının korunması ahlaki bir zorunluluktur. Kısa vadeli çıkarlar için gelecek feda edilemez. Uzun vadeli düşünme, sürdürülebilir politikaların temelidir. Nesiller arası adalet, toplumsal sorumluluğun gereğidir."
            },
        ]

        # Normal Yasalar (200 madde)
        laws = [
            # I. Anayasal Düzen (1-20)
            "Egemenlik kayıtsız şartsız milletindir. Hiçbir kişi, grup veya sınıf adına kullanılamaz.",
            "Devlet yapısı üniterdir. Yerel özerklikler tanınsa da bölünmez bütünlük esastır.",
            "Yasama yetkisi parlamentoya aittir. Parlamento, halkın doğrudan temsilcilerinden oluşur.",
            "Yürütme yetkisi bakanlar kuruluna aittir. Başbakan, parlamentonun güvenoyuyla göreve gelir.",
            "Yargı bağımsızdır. Hiçbir organ, makam, kişi veya kuruluş yargı yetkisinin kullanılmasında mahkemelere emir ve talimat veremez.",
            "Anayasa değişiklikleri referanduma tabidir. Anayasanın değişmez maddelerinde değişiklik yapılamaz.",
            "Vatandaşlık hakkı doğuştan kazanılır. Hiçbir Türk vatandaşı, vatandaşlıktan çıkarılamaz.",
            "Seçimler serbest, eşit, gizli, tek dereceli, genel oy ve açık sayım ilkelerine göre yapılır.",
            "Seçim barajı %3'tür. Demokratik temsili güçlendirmek için düşük baraj uygulanır.",
            "Milletvekili dokunulmazlığı sınırlıdır. Ağır suçlarda dokunulmazlık kaldırılabilir.",
            "Cumhurbaşkanı sembolik bir roldedir. Protokol görevleri yürütür, tarafsız kalır.",
            "Parlamento 400 üyeden oluşur. Dört yıl için seçilir, erken seçim çoğunlukla mümkündür.",
            "Bölgesel meclisler kurulmalıdır. Yerel sorunlar, yerel halk tarafından çözülmelidir.",
            "Belediye başkanları halk tarafından seçilir. Yerel yönetimler özerk bütçeye sahiptir.",
            "Kamu denetçiliği (Ombudsman) kurumu bağımsızdır. Vatandaş şikayetleri tarafsız incelenir.",
            "Referandum %10 imza ile başlatılabilir. Halkın doğrudan karar verme hakkı güçlendirilmiştir.",
            "Olağanüstü hal süresi sınırlıdır. Maksimum 3 ay olup, uzatma parlamentonun onayına tabidir.",
            "Meclis oturumları açıktır. Tüm görüşmeler canlı yayınlanır, tutanaklar herkese açıktır.",
            "Siyasi partilere devlet desteği vardır. Ancak şeffaflık zorunluluğu ve hesap verebilirlik gereklidir.",
            "Partilerin kapatılması son derece istisnaidir. Ancak şiddet çağrısı yapan partiler kapatılabilir.",

            # II. Temel Haklar ve Özgürlükler (21-50)
            "Düşünce özgürlüğü mutlaktır. Hiç kimse, düşüncelerinden dolayı kınanamaz, suçlanamaz.",
            "İfade özgürlüğü, şiddet çağrısı olmadıkça korunur. Sansür yasaktır.",
            "Basın özgürlüğü dokunulmazdır. Gazeteciler, kaynaklarını açıklamaya zorlanamaz.",
            "Örgütlenme özgürlüğü tüm vatandaşlara tanınmıştır. Dernekler ve vakıflar kolayca kurulabilir.",
            "Toplantı ve gösteri hakkı serbesttir. İzin alma zorunluluğu yoktur, yalnızca bildirim yeterlidir.",
            "Grev hakkı kısıtlanamaz. İşçilerin en temel hakkı olarak korunur.",
            "Lokavt yasaktır. İşverenler, grev kırıcı önlemler alamaz.",
            "Konut dokunulmazdır. Mahkeme kararı olmadan kimsenin evi aranamaz.",
            "Haberleşme özgürlüğü korunur. Telefon dinleme, e-posta izleme ancak ağır suç şüphesinde mümkündür.",
            "Seyahat özgürlüğü vardır. Hiç kimse, seyahat etmekten alıkonulamaz.",
            "Yerleşme özgürlüğü vardır. Herkes, dilediği yerde yaşayabilir.",
            "Din ve vicdan özgürlüğü mutlaktır. Hiç kimse, dini inancından dolayı ayrımcılığa uğramaz.",
            "Eğitim dili ana dildir. Azınlıklar, kendi dillerinde eğitim alabilir.",
            "Kültürel haklar tanınır. Tüm kültürel kimlikler devlet tarafından eşit kabul edilir.",
            "Eşcinsel evlilik meşrudur. Tüm bireyler, eşit evlilik hakkına sahiptir.",
            "Kürtaj haktır. Kadınlar, kendi bedenleri üzerinde karar verme özgürlüğüne sahiptir.",
            "Ötanazi koşullu olarak tanınır. Ağır hastalık durumunda onurlu ölüm hakkı vardır.",
            "Esrar kişisel kullanım için yasal olmalıdır. Bağımlılık sağlık sorunu olarak ele alınmalıdır.",
            "Kimlik kartında din bilgisi olmaz. Devlet, bireyin inancını kaydetmez.",
            "Zorunlu askerlik kaldırılmalıdır. Profesyonel ordu modeli benimsenmelidir.",
            "Vicdani ret hakkı tanınır. Kimse, inancına aykırı hizmete zorlanamaz.",
            "Pozitif ayrımcılık uygulanır. Dezavantajlı gruplar için kota sistemi vardır.",
            "Çocuk evliliği yasaktır. 18 yaş altı evlilik hiçbir şekilde kabul edilemez.",
            "Çocuğa şiddet yasaktır. Eğitim kurumlarında ve evde fiziksel ceza kesinlikle yasaklanmıştır.",
            "Evde eğitim hakkı tanınır. Veliler, çocuklarını devlet okuluna göndermek zorunda değildir.",
            "Anadil eğitim haktır. Kürtçe, Zazaca, Lazca gibi dillerde eğitim devlet tarafından desteklenir.",
            "Üniversiteler özerk ve özgür olmalıdır. Akademik özgürlük korunur, rektörler seçimle gelir.",
            "Öğrenciler yönetimde söz sahibidir. Üniversite yönetim kurullarında öğrenci temsilcileri bulunur.",
            "Eğitim ücretsizdir. Anaokulu, ilkokul, ortaokul, lise ve üniversite ücretsiz ve zorunludur.",
            "Özel okul teşviki kaldırılır. Devlet, kamusal eğitimi öncelemelidir.",

            # III. Ekonomik ve Sosyal Politika (51-100)
            "Asgari ücret, insanca yaşam standardını garanti eder. Yoksulluk sınırının altında olamaz.",
            "Haftalık çalışma süresi 35 saattir. Fazla mesai ücretleri yüksek oranda ödenir.",
            "Eşit işe eşit ücret ilkesi uygulanır. Kadın-erkek arasında ücret farkı olamaz.",
            "Kreş hizmeti ücretsizdir. Çalışan ebeveynlere devlet desteği sağlanır.",
            "Doğum izni 12 aydır. Ebeveynler arasında eşit paylaşılır ve ücretlidir.",
            "Emeklilik yaşı 60'tır. Ağır işlerde erken emeklilik hakkı tanınır.",
            "Emekli maaşları, enflasyona göre artırılır. Asgari emekli maaşı, yoksulluk sınırının üstündedir.",
            "İşsizlik maaşı 2 yıl süreyle verilir. İşsizlerin yeniden istihdam programları desteklenir.",
            "Sosyal yardım sistematiktir. İhtiyaç sahibi ailelere düzenli gelir desteği sağlanır.",
            "Vergide adalet esastır. Zenginler daha yüksek oranda vergi öder, fakirler muaf tutulur.",
            "Servet vergisi uygulanır. Büyük servetler üzerinden yıllık vergi alınır.",
            "Emlak vergisi artan oranlıdır. Birden fazla ev sahipleri yüksek oranda vergilendirilir.",
            "Kira artışı sınırlandırılmıştır. Yıllık kira artışı enflasyonu geçemez.",
            "Sosyal konut projesi yaygınlaştırılır. Devlet, düşük gelirli ailelere uygun fiyatlı konut sağlar.",
            "Kentsel dönüşüm zorla yapılamaz. Sakinlerin rızası ve katılımı zorunludur.",
            "İmar affı yasaktır. İmar kurallarına uymayan yapılar yıkılır.",
            "Maden arama ruhsatları halka açık ihaleyle verilir. Yabancı şirketlere ruhsat verilemez.",
            "Madenler çevresel etki değerlendirmesine tabidir. Halk sağlığını tehdit eden projeler reddedilir.",
            "Ormanlar kesinlikle korunur. Ormanlık alanlarda maden işletme ve yapılaşma yasaktır.",
            "Tarım arazileri koruma altındadır. Tarım arazileri imara açılamaz, satışı kısıtlıdır.",
            "Genetiği değiştirilmiş organizmalar (GDO) yasaktır. Tohum egemenliği savunulur.",
            "Küçük çiftçi desteklenir. Büyük arazi sahipleri yerine aile çiftçiliği teşvik edilir.",
            "Hayvancılık endüstriyel olmayan biçimde yapılır. Hayvan refahı standartları yüksektir.",
            "Balıkçılık kotaları bilimsel verilere dayanır. Aşırı avcılık yasaklanır.",
            "Orman köylülerine alternatif geçim kaynakları sağlanır. Köylüler, korumadan sorumlu tutulur.",
            "Enerji üretimi yerli kaynaklara dayanır. Rüzgar, güneş ve hidroelektrik teşvik edilir.",
            "Termik santraller kapatılır. Kömür ve doğal gaz yerine yenilenebilir enerjiye geçilir.",
            "Elektrik üretimi ve dağıtımı kamuya aittir. Özelleştirme geri alınır.",
            "Doğalgaz boru hatları millileştirilir. Stratejik altyapı özel şirketlere bırakılamaz.",
            "Ulaşım sübvanse edilir. Toplu taşıma ucuz ve erişilebilir olmalıdır.",
            "Yüksek hızlı tren ağı genişletilir. Havayolu yerine tren ulaşımı teşvik edilir.",
            "Otomobil kullanımı azaltılır. Şehir merkezlerinde özel araç kısıtlanır.",
            "Bisiklet yolları yaygınlaştırılır. Sürdürülebilir ulaşım desteklenir.",
            "Kargo taşımacılığı demiryoluna kaydırılır. Kamyon trafiği azaltılır.",
            "Havacılık vergilendirilir. Uçuş başına karbon vergisi uygulanır.",
            "İnternet erişimi temel haktır. Fiber internet tüm ülkeye ücretsiz sağlanır.",
            "Telekomünikasyon şirketleri millileştirilir. İletişim altyapısı kamu hizmeti olarak sunulur.",
            "Dijital mahremiyet korunur. Kişisel veri ticareti yasaktır.",
            "Yapay zeka düzenlenir. Otomasyon sonucu işsiz kalanlar korunur.",
            "Kripto para düzenlenir. Mali suç ve vergi kaçırma engellenir.",
            "Finans işlem vergisi uygulanır. Spekülatif işlemler vergilendirilir.",
            "Banka kurtarma yasaktır. Batık bankalar halka maliyet çıkartmaz.",
            "Merkez Bankası bağımsızdır. Hükümet, para politikasına müdahale edemez.",
            "Döviz spekülasyonu sınırlandırılır. Döviz alım-satımına sınır getirilir.",
            "Faiz oranları kontrol edilir. Tefecilik yasaktır, tüketici kredileri düzenlenir.",
            "Kart borcu afları düzenli yapılır. Faiz batağına düşenler kurtarılır.",
            "İcra takipleri insanca yapılır. Temel eşyalara haciz konulamaz.",
            "Tüketici hakları güçlendirilir. Aldatıcı reklamlar yasaklanır.",
            "Tekeller yasaklanır. Rekabet Kurumu güçlendirilir.",
            "Kamu ihaleleri şeffaftır. Torpil ve rüşvet sıfırlanır.",

            # IV. Sağlık ve Sosyal Güvenlik (101-130)
            "Sağlık hizmeti ücretsizdir. Hiç kimse muayene, tetkik veya ameliyat ücreti ödemez.",
            "Özel hastaneler kapatılır. Sağlık sisteminin tümü kamusallaştırılır.",
            "Aile hekimliği sistemi güçlendirilir. Önleyici sağlık hizmetleri yaygınlaştırılır.",
            "Eczaneler kooperatif esasına döndürülür. İlaç fiyatları devlet tarafından belirlenir.",
            "İlaç üretimi millileştirilir. Patent hakları halk sağlığı için aşılır.",
            "Aşılar zorunludur. Bilimsel verilerle desteklenen aşılar tüm çocuklara uygulanır.",
            "Ruh sağlığı hizmetleri ücretsizdir. Psikolojik destek herkese açıktır.",
            "Bağımlılık tedavisi kamusal hizmettir. Madde bağımlılığı suç değil, sağlık sorunudur.",
            "Kanser taramaları ücretsiz ve yaygındır. Erken teşhis programları desteklenir.",
            "Diş tedavisi ücretsizdir. Ağız ve diş sağlığı genel sağlık hizmetine dahildir.",
            "Gözlük ve işitme cihazı ücretsizdir. Görme ve işitme engellilere devlet desteği sağlanır.",
            "Tamamlayıcı tıp düzenlenir. Bilimsel olmayan tedaviler yasaklanır.",
            "Hastane enfeksiyonları sıfırlanır. Hijyen standartları yükseltilir.",
            "Acil sağlık hizmetleri 5 dakikada ulaşır. Ambulans sayısı artırılır.",
            "Yaşlı bakım evleri kamusallaştırılır. Özel huzurevlerinde kötü muamele engellenir.",
            "Evde bakım destekleri artırılır. Ailelere bakıcı ve maddi destek sağlanır.",
            "Kadın sağlığı önceliktir. Doğum kontrol yöntemleri ücretsizdir.",
            "Anne ölümleri sıfırlanır. Doğum öncesi ve sonrası takip yaygınlaştırılır.",
            "Bebek ölümleri sıfırlanır. Neonatal yoğun bakım üniteleri yaygınlaştırılır.",
            "Aşı takvimi genişletilir. Yeni hastalıklar için aşı çalışmaları hızlandırılır.",
            "Obezite ile mücadele başlatılır. Okullarda sağlıklı beslenme programları uygulanır.",
            "Tütün ürünleri ağır vergilendirilir. Sigara reklamları tamamen yasaklanır.",
            "Alkol satışı düzenlenir. Gençlere satış yasaklanır, kamu reklamları yasaktır.",
            "Spor yapma teşvik edilir. Halka açık spor tesisleri ücretsizdir.",
            "Kamu çalışanlarına yıllık sağlık taraması yapılır. İş sağlığı ve güvenliği sıkı denetlenir.",
            "Meslek hastalıkları tazmin edilir. İşverenler sorumlu tutulur.",
            "İş kazaları sıfırlanır. Güvenliksiz çalışma durdurulan işyerleri kapatılır.",
            "Zehirli kimyasallar yasaklanır. Üretim ve ithalat denetlenir.",
            "Hava kalitesi standartları yükseltilir. Kirletici tesisler kapatılır.",
            "Gürültü kirliliği azaltılır. Şehir planlaması sessiz alanlar oluşturur.",

            # V. Adalet ve Hukuk (131-160)
            "Masumiyet karinesi esastır. Kimse, suçluluğu kanıtlanana kadar suçlu sayılamaz.",
            "Adil yargılanma hakkı vardır. Herkes, bağımsız ve tarafsız mahkemede yargılanır.",
            "Avukata erişim hakkı sınırsızdır. Gözaltında bile avukat bulundurma hakkı vardır.",
            "İşkence mutlak yasaktır. İşkence yapanlar ağır ceza alır.",
            "Gözaltı süresi maksimum 24 saattir. Uzatma ancak savcı kararıyla mümkündür.",
            "Tutuklamanın gerekçesi açıkça belirtilmelidir. Keyfi tutuklama yasaktır.",
            "Cezaevleri ıslah amacıyla çalışır. İnsan onuruna uygun koşullar sağlanır.",
            "Ölüm cezası yasaktır. İdam hiçbir suç için uygulanamaz.",
            "Müebbet hapis koşullu olmalıdır. 25 yıl sonra yeniden değerlendirme yapılır.",
            "Çocuklar cezaevine giremez. Çocuk suçlular rehabilitasyon merkezine gönderilir.",
            "Kadın cezaevleri ayrıdır. Hamile ve emziren annelere özel haklar tanınır.",
            "Cezaevi ziyaretleri kolaylaştırılır. Aile bağları korunur.",
            "Mahkumlara eğitim hakkı tanınır. Cezaevlerinde kütüphane ve kurslar açılır.",
            "Oy hakkı mahkumlara da tanınır. Tutuklu ve hükümlüler seçimlerde oy kullanır.",
            "Af yasası düzenli çıkar. Küçük suçlarda hapis cezası ertelenir.",
            "Şartla tahliye kolaylaştırılır. İyi halliler ceza süresinin yarısında salıverilir.",
            "Elektronik kelepçe yaygınlaştırılır. Hapis yerine denetimli serbestlik tercih edilir.",
            "Toplum hizmeti cezası yaygınlaşır. Hapishane yerine sosyal katkı sağlanır.",
            "Para cezaları gelire göre belirlenir. Zengin ve fakir eşit ceza alır.",
            "Hukuki yardım ücretsizdir. Yoksullar için devlet avukatı sağlanır.",
            "Arabuluculuk teşvik edilir. Dava açmadan anlaşma sağlanır.",
            "Mahkeme masrafları azaltılır. Adalete erişim kolaylaştırılır.",
            "Duruşmalar makul sürede sonuçlanır. Yargının gecikmesi adaletin reddidir.",
            "Yargıtay ve Danıştay üyeleri seçimle gelir. Atama yerine şeffaf seçim yapılır.",
            "Anayasa Mahkemesi üyeleri karma sistemle seçilir. Parlamentonun ve meslek kuruluşlarının onayı gerekir.",
            "Hakim ve savcılar sendikalaşabilir. Yargı mensuplarının örgütlenme hakkı vardır.",
            "Yargı bağımsızlığını bozan her müdahale suçtur. Siyasi baskı ağır cezalandırılır.",
            "Özel kanun yolları kaldırılır. Askeri, çocuk ve basın mahkemeleri genel yargıya dahil edilir.",
            "Jüri sistemi ceza davalarında uygulanır. Halk, yargı kararlarına katılır.",
            "Hakimler açık kimlikle karar verir. Anonim kararlar yasaklanır.",

            # VI. Dış Politika ve Savunma (161-180)
            "Dış politika barışçıdır. Savaş, yalnızca savunma amacıyla meşrudur.",
            "NATO'dan çıkış planlanır. Askeri ittifaklar yerine tarafsızlık politikası benimsenir.",
            "Yabancı üsler kapatılır. Ulusal egemenlik korunur.",
            "Nükleer silah yasaktır. Ülke topraklarında nükleer silah bulundurulamaz.",
            "Silah ticareti kısıtlanır. İnsan hakları ihlali yapan ülkelere silah satışı yasaktır.",
            "Asker sayısı azaltılır. Profesyonel ordu modeline geçilir.",
            "Savunma bütçesi düşürülür. Kaynak, sağlık ve eğitime aktarılır.",
            "Silah sanayii kamuya aittir. Özel şirketler silah üretemez.",
            "Barış ve diyalog önceliktir. Komşu ülkelerle işbirliği güçlendirilir.",
            "Mültecilere insani muamele edilir. Geri gönderme yasaktır, entegrasyon desteklenir.",
            "Uluslararası hukukun üstünlüğü kabul edilir. BM kararları uygulanır.",
            "İnsan hakları ihlallerinde taraf olunmaz. Soykırım ve işgallere karşı duruş sergilenir.",
            "Filistin davası desteklenir. İsrail'in işgalci politikalarına karşı çıkılır.",
            "Kürt sorununa demokratik çözüm aranır. Diyalog ve müzakere sürdürülür.",
            "Kıbrıs sorunu barışçıl çözülür. İki toplumlu federal yapı desteklenir.",
            "Ege sorunları uluslararası hukuka göre çözülür. Türkiye-Yunanistan gerginliği azaltılır.",
            "Su paylaşımı adildir. Sınır aşan sular komşu ülkelerle paylaşılır.",
            "Kültürel diplomasi güçlendirilir. Sanat, bilim ve eğitim işbirliği artırılır.",
            "Diaspora ile bağlar güçlendirilir. Yurtdışındaki vatandaşlara destek sağlanır.",
            "Uluslararası öğrenci değişimi teşvik edilir. Eğitimde küresel işbirliği desteklenir.",

            # VII. Bilim, Teknoloji ve İnovasyon (181-200)
            "Bilimsel araştırmaya GSYH'nin %3'ü ayrılır. AR-GE desteklenir.",
            "Üniversite-sanayi işbirliği güçlendirilir. Yerli teknoloji geliştirilir.",
            "Patent hakları halka açılır. Temel ilaç ve teknolojilerde patent sınırlaması yapılır.",
            "Açık kaynak yazılım desteklenir. Kamu kurumları özgür yazılım kullanır.",
            "Yapay zeka etik kurallara bağlanır. Algoritmik ayrımcılık yasaktır.",
            "Veri egemenliği savunulur. Vatandaşların verileri yurt dışına çıkarılamaz.",
            "Uzay programı başlatılır. Bilimsel amaçlı uydu ve araştırma projelerine yatırım yapılır.",
            "Denizaltı kaynakları araştırılır. Mavi vatan konseptinde bilimsel çalışmalar yapılır.",
            "İklim bilimi desteklenir. İklim krizi ile mücadelede bilime dayalı politikalar uygulanır.",
            "Biyoteknoloji yatırımları artırılır. Yerli ilaç ve aşı üretimi teşvik edilir.",
            "Nanoteknoloji araştırmaları yapılır. Gelecek teknolojilerinde öncü olunur.",
            "Kuantum bilişim desteklenir. Teknolojik bağımsızlık için yatırım yapılır.",
            "5G altyapısı hızla kurulur. Dijital dönüşüm hızlandırılır.",
            "Siber güvenlik önceliktir. Ulusal siber savunma altyapısı oluşturulur.",
            "Blockchain teknolojisi kamu hizmetlerinde kullanılır. Şeffaflık artırılır.",
            "Dijital okuryazarlık zorunludur. Kodlama eğitimi ilkokuldan başlar.",
            "E-devlet hizmetleri yaygınlaştırılır. Bürokratik işlemler dijitalleşir.",
            "Açık veri politikası benimsenir. Kamu verileri halka açılır.",
            "Bilim merkezleri yaygınlaştırılır. Çocuklar bilimle erken tanışır.",
            "Bilim olimpiyatları desteklenir. Yetenekli öğrenciler teşvik edilir.",
        ]

        # Kuruluş ilkelerini ekle
        self.stdout.write('Kuruluş ilkeleri ekleniyor...')
        for i, principle in enumerate(foundation_principles, 1):
            DoctrineArticle.objects.get_or_create(
                article_type='FOUNDATION_LAW',
                article_number=i,
                defaults={
                    'content': principle['content'],
                    'justification': principle['justification'],
                    'created_by': founder
                }
            )
        self.stdout.write(self.style.SUCCESS(f'{len(foundation_principles)} kuruluş ilkesi eklendi'))

        # Normal yasaları ekle
        self.stdout.write('Normal yasalar ekleniyor...')
        for i, content in enumerate(laws, 1):
            DoctrineArticle.objects.get_or_create(
                article_type='NORMAL_LAW',
                article_number=i,
                defaults={
                    'content': content,
                    'created_by': founder
                }
            )
        self.stdout.write(self.style.SUCCESS(f'{len(laws)} yasa eklendi'))

        self.stdout.write(self.style.SUCCESS('Doktrin başarıyla dolduruldu!'))
