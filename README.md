# AI DÜNYA — Türkçe ve kaynaklı küresel yapay zekâ haberleri

Kendi sunucunuzu kiralamadan GitHub Pages üzerinde yayımlanabilen, her gün uluslararası RSS/Atom kaynaklarından haber derleyen örnek site.

## 5 dakikada yayına alma

1. GitHub üzerinde **public** (herkese açık) bir depo oluşturun; örneğin `ai-dunya`.
2. Bu ZIP içindeki **tüm dosyaları**, gizli `.github` klasörü dahil, deponun ana dizinine yükleyin. ZIP'i tek dosya olarak yüklemeyin; içeriğini çıkarın. GitHub Web arayüzünde gizli klasör yüklenmesi sorun çıkarırsa GitHub Desktop ile kopyalayın.
3. Depoda **Settings → Pages → Build and deployment → Source: Deploy from a branch** seçin, `main` ve `/(root)` ayarlayıp Save'e basın.
4. **Actions** sekmesinde **Günlük AI haberlerini topla** iş akışını açıp **Run workflow** çalıştırın. İşlem tamamlanınca `data/news.json` içerik kazanır.
5. `https://KULLANICIADI.github.io/ai-dunya/` adresini açın. Deponuzun adı farklıysa URL de değişir.
6. İş akışının `git push` aşamasında izin hatası olursa Settings → Actions → General → Workflow permissions altında **Read and write permissions** açın (kurum kuralları bunu sınırlayabilir).

### Otomatik zamanlama

`.github/workflows/daily.yml` dosyasındaki `cron: '17 5 * * *'` her gün UTC 05:17, Türkiye saatiyle 08:17 hedefler. GitHub iş akışlarını yoğunlukta geciktirebilir, bazı koşullarda atlayabilir; uzun süre etkin olmayan public depolarda schedule devre dışı kalabilir. `workflow_dispatch` ile manuel yenileyebilirsiniz.

### Yerelde denemek

```bash
python -m pip install -r requirements.txt
python collect.py
python -m http.server 8000
```

Tarayıcıda `http://localhost:8000` açın. `index.html` dosyasını doğrudan çift tıklayarak açmak, tarayıcının yerel dosya güvenliği nedeniyle JSON yüklemeyebilir.

## Doğrulama yaklaşımı ve sınırları

- Her yazıda orijinal kaynağa **gerçek bağlantı** bulunur.
- Başlık benzerliği belirli bir eşiği geçerse farklı yayıncılara bağlantılar eklenir. Algoritma aynı olayla ilgili haberleri kaçırabilir veya benzer fakat farklı olayları yanlış gruplayabilir.
- "Birden fazla bağımsız yayıncıda bulundu" ifadesi **iddianın doğrulandığı anlamına gelmez**. Kaynakların birbirini kopyalayıp kopyalamadığı denetlenmez.
- Resmî şirket açıklamaları birincil kaynaktır; bağımsız gerçeklik teyidi değildir.
- arXiv kayıtları ön baskı olabilir; bağımsız hakem değerlendirmesi veya sonuçların yeniden üretilmesi otomatik kontrol edilmez.
- Tek kaynaklı gelişmeler "Ek doğrulama gerekiyor" etiketiyle gösterilir.
- Bu bir **otomatik haber derleyicisidir, profesyonel fact-checking servisi değildir**. Doğruluk kritikse bağlantılardan asıl belge, metodoloji ve bağımsız haberler ayrıca incelenmelidir.

## Çeviri ve ücretler

`deep-translator` çevrimiçi kamuya açık çeviri arayüzünü kullanır; ücretsiz kullanım kesin garanti edilmez, hız sınırlamalarına ve üçüncü taraf hizmet değişikliklerine tabidir. Çeviri başarısızsa sistem **orijinal dilde bırakır ve işaretler**, gerçek olmayan Türkçe metin üretmez. Daha güvenilir üretim için izinli bir çeviri API'si eklenebilir. İçerikler otomatik kısaltılır, tam haber kopyalanmaz.

GitHub Pages ve GitHub Actions'ın ücretsiz kullanım için limit ve hizmet şartları vardır. Public depodaki Actions kullanımının normal GitHub-hosted koşulları ücretsiz olabilir; kişisel plan/kurum kısıtları değişebilir.

## Ayarlar

- `sources.json`: Kaynaklar ve kaynak türleri (`resmi`, `bagimsiz`, `onbaski`).
- `.github/workflows/daily.yml`: Güncelleme saati ve otomasyon.
- `collect.py`: Başlık eşleştirme, kategoriler, çeviri ve haber işleme.
- `style.css`: Renkler ve tasarım.
- `WINDOW_DAYS` (varsayılan 10): Kaç günlük haber taranacak.
- `MAX_ITEMS` (varsayılan 120): JSON'a yazılacak haber sayısı.
- `TRANSLATE=0`: Çeviriyi kapatır.

## Güvenlik ve kaynak hakları

Sadece yayınların RSS/Atom üzerinden sunduğu kısa metinler kullanılır. Özetler ve kaynak URL'leri gösterilir. Kaynakların telif, robots/erişim ve kullanım koşullarına uyulmalıdır. Haber kaynağının ilk RSS alanında yer almayan detaylar oluşturulmaz. Kaynak bağlantıları yeni sekmede açılır ve HTML içerikleri kaçışlanır. Bu yazılım hiçbir haberi "kesin doğrulandı" olarak etiketlemez.

## Yeni tasarım (v2)

- Koyu renkli, iki sütunlu ana sayfa: büyük manşet, kaynak/doğrulama paneli, gündem kartları, sağ günlük özet ve haber kategorilerine dayalı trend listesi.
- Haber kaydı henüz yoksa sayfa **ÖRNEK GÖRÜNÜM** bandıyla beş temsili kart gösterir. Bu kartlar gerçek haber değildir, gerçek kaynak veya teyit sonucu içermez; `data/news.json` dolunca otomatik kaybolurlar.
- Haber ayrıntısında kaynak bağlantıları açılabilir; günün özeti kopyalanabilir; arama ve kategori filtreleri çalışır.
- Trend konular, arayüzde yüklü haber kategorilerinin sayımıdır; kamuya açık arama hacmi ölçümü değildir.
- Bu sürümde görsel başlık alanları CSS ile üretilmiştir. Dış resim sunucusu veya API anahtarı gerektirmez.
- Görsel tasarımdaki e-posta gönderimi yerine **Günlük Özeti Kopyala** kullanılır; bir e-posta gönderme altyapısı kurulmuş gibi davranılmaz.
