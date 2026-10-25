# Enterprise Backend & Automation Engine

FastAPI tabanlı; görev yönetimi, BI raporlama, belge işleme, RAG bilgi bankası ve güvenli webhook otomasyonunu tek bir production-oriented serviste birleştiren sistem.

## Mimari

```text
API endpoints → Core (security/config/logging) → Services → Async SQLAlchemy → PostgreSQL
                                                     └──── Celery + Redis
```

| Alan | Sağlanan özellik |
|---|---|
| Task & Workflow | JWT, Argon2 parola hashleme, RBAC, sahiplik, filtreleme, sayfalama ve tanımlanabilir workflow kaynakları |
| BI | Pandas analizi, ReportLab PDF ve Celery Beat ile günlük cron raporu |
| Document | PDF/DOCX/TXT doğrulama, boyut sınırı, metin/meta veri ayıklama |
| RAG | Veritabanı tabanlı bağlam getirme ve Google Gemini yanıt üretimi |
| Webhook | HMAC-SHA256, idempotency key ve asenkron dış bildirim |

## Docker ile çalıştırma

1. `.env.example` dosyasını `.env` olarak kopyalayın ve sırları değiştirin.
2. Başlatın:

```bash
docker compose up --build
```

Swagger arayüzü: `http://localhost:8000/docs`  
Sağlık kontrolü: `http://localhost:8000/health`

Stack; API, Celery worker, Celery Beat, PostgreSQL ve Redis servislerini içerir. Upload ve rapor klasörleri hosta bağlanır.

## Yerel geliştirme

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -e ".[dev]"
copy .env.example .env
uvicorn app.main:app --reload
pytest
```

Worker'ları yerelde ayrıca başlatmak için:

```bash
celery -A app.workers.celery_app worker --loglevel=INFO
celery -A app.workers.celery_app beat --loglevel=INFO
```

## API akışı

1. `POST /api/v1/auth/register` ile kullanıcı oluşturun.
2. `POST /api/v1/auth/login` OAuth2 form verisi kullanır (`username` alanı e-postadır).
3. Korunan rotalara `Authorization: Bearer <token>` ekleyin.
4. Görev rotaları: `/api/v1/tasks`; üyeler sadece kendi görevlerini görür. Yönetici/manager rolü `/api/v1/workflows` üzerinden workflow tanımı oluşturabilir.
5. Belge yükleyin: `POST /api/v1/documents`; sonra `POST /api/v1/knowledge/ask` çağırın.
6. Yönetici/manager kullanıcılar `POST /api/v1/reports` ile PDF işini kuyruğa alır.

## Webhook güvenliği

Ham gövdeyi `HMAC-SHA256(WEBHOOK_SECRET, raw_body)` ile imzalayın ve hexadecimal sonucu `X-Signature` başlığında gönderin. Her istekte benzersiz `Idempotency-Key` gerekir. Hedef rota `POST /api/v1/webhooks/{event_type}`; tekrar eden anahtarlar yeniden işlenmez.

## Üretim notları

- Sırları secret manager üzerinden yönetin; TLS, sınırlı CORS ve Alembic migration kullanın.
- Büyük ölçekli yüklemelerde object storage ve antivirüs taraması ekleyin.
- `GEMINI_API_KEY` ayarlandığında Gemini devreye girer; aksi halde güvenli bağlam fallback'i döner.
- Loglar merkezi toplanmaya uygun JSON biçiminde stdout'a yazılır.
