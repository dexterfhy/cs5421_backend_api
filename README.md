### Dependencies

- Assuming pip is installed, run `pip install -r requirements.txt`

### Environment Variables

Create a `.env` file with key-value pairs for the following variables:
- `DB_USER`
- `DB_PASS`
- `DB_HOST`
- `DB_PORT`

### Database

- Run `migration.sql`

### Django Setup

```
python manage.py migrate
python manage.py createsuperuser
```