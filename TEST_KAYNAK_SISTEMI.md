# Kaynak Ekleme Sistemi - Test Kılavuzu

## ✅ Tamamlanan Özellikler

### 1. Backend (Models & Views)
- ✅ `Reference` modeli - Kaynak bilgilerini tutar
- ✅ `ProposalReference` modeli - Öneri-Kaynak ilişkisi
- ✅ `ArticleReference` modeli - Madde-Kaynak ilişkisi
- ✅ API Endpoints:
  - `/doctrine/api/references/create/` - Yeni kaynak oluştur
  - `/doctrine/api/references/list/` - Tüm kaynakları listele
  - `/doctrine/api/references/my-references/` - Kullanıcının kaynakları
  - `/doctrine/api/references/<id>/usage/` - Kaynağın kullanım yerleri
  - `/doctrine/references/` - Kaynaklar sayfası

### 2. Frontend (JavaScript & Templates)
- ✅ `reference-manager.js` - Kaynak yönetimi için JavaScript
- ✅ Modal sistemi - Yeni kaynak ekleme ve mevcut kaynak seçme
- ✅ `create_proposal.html` - Öneri oluştururken kaynak ekleme
- ✅ `proposal_detail.html` - Öneride kaynakları görüntüleme

### 3. Stil (CSS)
- ✅ Kaynak ekleme modal stilleri
- ✅ Seçili kaynaklar listesi stilleri
- ✅ Proposal detail'de kaynak gösterim stilleri

## 📝 Test Adımları

### Adım 1: Yeni Kaynak Oluşturma
1. http://127.0.0.1:8000/doctrine/proposal/create/ sayfasına git
2. Gerekçe alanının altında "📚 Yeni Kaynak Ekle" butonuna tıkla
3. Modal açılır, "Yeni Kaynak Oluştur" sekmesinde:
   - Kaynak Türü: Kitap
   - Yazar: Kant, Immanuel
   - Başlık: Praktik Aklın Eleştirisi
   - Yıl: 1788
   - Yayınevi: Felix Meiner Verlag
   - Sayfa: s.157
4. "Kaydet ve Ekle" butonuna tıkla
5. Kaynak "Seçili Kaynaklar" bölümünde görünmeli

### Adım 2: Mevcut Kaynak Seçme
1. "📚 Yeni Kaynak Ekle" butonuna tekrar tıkla
2. "Mevcut Kaynak Seç" sekmesine geç
3. Listeden bir kaynak seç
4. Kaynak "Seçili Kaynaklar" bölümüne eklenmeli

### Adım 3: Kaynaklar Sayfası
1. http://127.0.0.1:8000/doctrine/references/ sayfasına git
2. Tüm kaynakları görmeli
3. "Kaynaklar" butonundan kaynakları hızlıca seçebilmeli

### Adım 4: Atıf Ekleme
1. Öneri oluştururken gerekçe alanına yazarken
2. Seçili kaynaklardan "Atıf Ekle" butonuna tıkla
3. Metin içine otomatik "(Kant, 1788, s.157)" formatında atıf eklenmeli

### Adım 5: Öneri Oluştur ve Görüntüle
1. Öneriyi oluştur
2. Öneri detay sayfasında "📚 Kaynakça" bölümünü gör
3. Kaynaklar bibliyografik formatta görünmeli

## 🔍 Test Sonuçları

### API Testleri
```bash
# Kaynak listesi
curl http://127.0.0.1:8000/doctrine/api/references/list/

# Yeni kaynak oluştur (POST ile test et)
# Tarayıcıda öneri oluştururken test edilecek
```

### Frontend Testleri
- [ ] Modal açılıyor mu?
- [ ] Kaynak formu çalışıyor mu?
- [ ] Kaynak seçimi çalışıyor mu?
- [ ] Atıf ekleme çalışıyor mu?
- [ ] Seçili kaynaklar görünüyor mu?

### Backend Testleri
- [x] API'lar çalışıyor mu?
- [x] Model ilişkileri doğru mu?
- [x] Kaynaklar veritabanına kaydediliyor mu?

## 🚀 Kalan İşler

### Maddelerde Kaynak Gösterimi
- [ ] `doctrine_list.html` - Maddelerde kaynakları göster
- [ ] Madde detay sayfasında kaynakları göster

### Gelişmiş Özellikler
- [ ] Kaynak düzenleme
- [ ] Kaynak silme (sadece oluşturan veya admin)
- [ ] Kaynak arama ve filtreleme
- [ ] DOI/ISBN otomatik çözümleme
- [ ] BibTeX export
- [ ] Atıf formatları (APA, MLA, Chicago, vb.)

## 💡 Kullanım Önerileri

1. **Yeni Kaynak Ekleme**: Eğer kaynak ilk kez kullanılıyorsa "Yeni Kaynak Oluştur" sekmesini kullan
2. **Mevcut Kaynak**: Kaynak daha önce eklendiyse "Mevcut Kaynak Seç" sekmesini kullan
3. **Atıf Yapma**: Gerekçe yazarken ilgili kaynaklara atıf yap
4. **Sayfa Numarası**: Spesifik bir sayfadan alıntı yapıyorsan sayfa numarasını belirt

## 📚 Örnek Kaynaklar

```
1. Kitap
   - Yazar: Kant, Immanuel
   - Başlık: Praktik Aklın Eleştirisi
   - Yıl: 1788
   - Yayınevi: Felix Meiner Verlag

2. Makale
   - Yazar: Rawls, John
   - Başlık: Justice as Fairness
   - Yıl: 1958
   - Dergi: Philosophical Review

3. Web Sitesi
   - Yazar: Stanford Encyclopedia of Philosophy
   - Başlık: Democracy
   - Yıl: 2023
   - URL: https://plato.stanford.edu/entries/democracy/
```

## ⚠️ Bilinen Sorunlar

- Henüz kaynak düzenleme özelliği yok
- Kaynak silme sadece admin panelden yapılabilir
- Atıf formatı şu an sadece (Yazar, Yıl, Sayfa) şeklinde

## 🎯 Sonraki Hedefler

1. Maddelerde kaynakları gösterme
2. Kaynak detay sayfası
3. Kaynak istatistikleri (en çok kullanılan kaynaklar, vb.)
4. Kaynak kalitesi onaylama sistemi (verified kaynaklar)
