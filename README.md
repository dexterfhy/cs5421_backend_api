### Dependencies

- Assuming pip is installed, run `pip install -r requirements.txt`

### Environment Variables

Create a `.env` file with key-value pairs for the following variables:
- `DB_USER`
- `DB_PASS`
- `DB_HOST`
- `DB_PORT`
- `KAFKA_BOOTSTRAP_SERVERS`
- `KAFKA_CLIENT_ID`
- `KAFKA_CONSUMER_GROUP_ID`
- `KAFKA_JOB_INIT_TOPIC`
- `KAFKA_JOB_ATTEMPT_FAST_TOPIC`
- `KAFKA_JOB_ATTEMPT_SLOW_TOPIC`
- `KAFKA_JOB_INIT_COMPLETION_TOPIC`
- `KAFKA_JOB_ATTEMPT_COMPLETION_TOPIC`

### Kafka Setup

- Download [Zookeeper](https://zookeeper.apache.org/releases.html) and [Kafka](https://kafka.apache.org/downloads)
- Start both with `zkserver` and `kafka-server-start`
- Create topics named under `KAFKA_JOB_INIT_TOPIC`, `KAFKA_JOB_ATTEMPT_FAST_TOPIC`, `KAFKA_JOB_ATTEMPT_SLOW_TOPIC`, `KAFKA_JOB_INIT_COMPLETION_TOPIC`, and `KAFKA_JOB_ATTEMPT_COMPLETION_TOPIC`
```
kafka-topics --bootstrap-server <host, usually localhost:9092> --create --replication-factor 1 --partitions 3 --topic=<name>
```

### Django Setup

```
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

To run:
```
python manage.py runserver
```

### Database Schema

#### Tables 

- Users
- Challenges
- TestCases
- Attempts
- AttemptedCases

See [relationships](https://drive.google.com/file/d/1Ufm9CTOjZX--RLCklymqB7MUn6zSx5os/view?usp=sharing)

### API Specs

#### Structure

All `200 OK` responses will return:
```
{
    "status": "success",
    "data": [...] or {...}
}
```

Error responses will return:
```
{
    "status": "error",
    "mesage": "Some error message"
}
```

#### Endpoints

- `POST register` - Creates a new `user`
```
{
    "email": "dexter@gmail.com",
    "full_name": "Dexter",
    "role": "PROF", //or 'STUD'
    "unsafe_password": "pass"
}
...
{
    "status": "success",
    "data": {
        "id": 4,
        "email": "dexter@gmail.com",
        "full_name": "Dexter",
        "unsafe_password": "pass",
        "created_at": "2022-03-17T08:14:05.660810Z"
    }
}
```

- `POST login` - Gets `user` by email and password
```
{
    "email": "dexter@gmail.com",
    "unsafe_password": "pass"
}
...
{
    "status": "success",
    "data": {
        "id": 3,
        "email": "dexter@gmail.com",
        "full_name": "Dexter",
        "unsafe_password": "pass",
        "created_at": "2022-03-17T08:13:54.982086Z"
    }
}
```

- `GET users/:user_id` - Gets `user` by user ID
```
{
    "status": "success",
    "data": {
        "id": 3,
        "email": "dexter@gmail.com",
        "full_name": "Dexter",
        "unsafe_password": "pass",
        "created_at": "2022-03-17T08:13:54.982086Z"
    }
}
```

- `GET users/:user_id/attempts/:attempt_id` - Gets `attempt` by user ID and attempt ID
```
{
    "status": "success",
    "data": {
        "id": 23,
        "user_id": 3,
        "challenge_id": 1,
        "query": "<SELECT statements...>",
        "created_at": "2022-03-25T09:53:27.764581Z",
        "attempts": [
            {
                "id": 17,
                "attempt_id": 36,
                "test_case_id": 1,
                "execution_ms": null,
                "created_at": "2022-03-25T09:53:28.105193Z",
                "status": "PENDING",
                "is_visible": false
            },
            {
                "id": 16,
                "attempt_id": 36,
                "test_case_id": 2,
                "execution_ms": 0,
                "expected_result": "{ some_serialized_JSON_string_of_results }",
                "actual_result": "{ some_serialized_JSON_string_of_results }",
                "created_at": "2022-03-25T09:53:27.935698Z",
                "status": "PENDING",
                "is_visible": true
            }
        ]
    }
}
```

- `GET challenges` - Gets all `challenges`
```
{
    "status": "success",
    "data": [
        {
            "id": 1,
            "created_user_id": 1,
            "name": "Test challenge",
            "description": "Test description",
            "type": "FE",
            "init": "<CREATE DATABASE...>",
            "init_at": "2022-03-25T17:30:28.933638Z",
            "init_errors": null,
            "solution": "<SELECT ...>",
            "times_to_run": 10,
            "test_cases": [
                {
                    "id": 1,
                    "challenge_id": 1,
                    "data": "<INSERT ...>",
                    "is_visible": true,
                    "created_at": "2022-03-17T00:00:00Z"
                },
                {
                    "id": 2,
                    "challenge_id": 1,
                    "data": "<INSERT ...>",
                    "is_visible": false,
                    "created_at": "2022-03-17T00:00:00Z"
                }
            ],
            "created_at": "2022-03-17T00:00:00Z"
        }
    ]
}
```

- `POST challenges` - Creates a new `challenge`
```
{
    "user_id": 1,
    "name": "Fabian Pascal",
    "description": "Some description", //Optional
    "type": "FE", //or 'SE' representing fastest/slowest execution types
    "init": "<CREATE DATABASE...>",
    "expires_at": "2022-06-01T12:00",
    "solution": "<SELECT ...>",
    "times_to_run": 10,
    "test_cases": [
        {
            "data": "<INSERT ...>",
            "is_visible": true
        },
        {
            "data": "<INSERT ...>",
            "is_visible": false
        }
    ]
}
...
{
    "status": "success",
    "data": {
        "id": 2,
        "created_user_id": 1,
        "name": "Fabian Pascal",
        "description": "Some description",
        "type": "FE",
        "init": "<CREATE DATABASE...>",
        "init_at": null,
        "init_errors": null,
        "solution": "<SELECT ...>",
        "times_to_run": 10,
        "created_at": "2022-03-17T08:21:21.002851Z"
    }
}
```
  
- `GET challenges/:challenge_id` - Gets `challenge` by challenge ID
```
{
    "status": "success",
    "data": {
        "id": 2,
        "created_user_id": 1,
        "name": "Fabian Pascal",
        "description": "Some description",
        "type": "FE",
        "init": "<CREATE DATABASE...>",
        "init_at": "2022-03-25T17:30:28.933638Z",
        "init_errors": null,
        "solution": "<SELECT ...>",
        "times_to_run": 10,
        "test_cases": [
            {
                "id": 1,
                "challenge_id": 2,
                "data": "<INSERT ...>",
                "is_visible": true,
                "created_at": "2022-03-17T00:00:00Z"
            },
            {
                "id": 2,
                "challenge_id": 2,
                "data": "<INSERT ...>",
                "is_visible": false,
                "created_at": "2022-03-17T00:00:00Z"
            }
        ],
        "created_at": "2022-03-17T08:21:21.002851Z",
        "top_attempts": [
            {
                "test_case_id": 23,
                "user_full_name": "Dexter Fong",
                "completion_time_ms": 100,
                "time_of_attempt": "2022-03-27T11:21:57.673975Z"
            },
            {
                "test_case_id": 24,
                "user_full_name": "Yu Yisong",
                "completion_time_ms": 50,
                "time_of_attempt": "2022-03-27T11:32:51.032865Z"
            }
        ]
    }
}
```
  
- `GET challenges-by-user/:challenge_id` - Gets `challenge` by user ID
```
{
    "status": "success",
    "data": {
        "id": 2,
        "created_user_id": 1,
        "name": "Fabian Pascal",
        "description": "Some description",
        "type": "FE",
        "init": "<CREATE DATABASE...>",
        "init_at": "2022-03-25T17:30:28.933638Z",
        "init_errors": null,
        "solution": "<SELECT ...>",
        "times_to_run": 10,
        "test_cases": [
            {
                "id": 1,
                "challenge_id": 2,
                "data": "<INSERT ...>",
                "is_visible": true,
                "created_at": "2022-03-17T00:00:00Z"
            },
            {
                "id": 2,
                "challenge_id": 2,
                "data": "<INSERT ...>",
                "is_visible": false,
                "created_at": "2022-03-17T00:00:00Z"
            }
        ],
        "created_at": "2022-03-17T08:21:21.002851Z"
    }
}
```

- `POST attempts` - Creates a new `attempt`
```
{
    "user_id": 1,
    "challenge_id": 1,
    "query": "<SELECT statements...>"
}
...
{
    "status": "success",
    "data": {
        "id": 24,
        "user_id": 1,
        "challenge_id": 1,
        "query": "<SELECT statements...>",
        "created_at": "2022-03-17T08:22:08.687418Z"
    }
}
```

### Kafka Specs

- `backend-api` publishes `JobInitEvent` to `backend-job` via `KAFKA_JOB_INIT_TOPIC`
- `backend-api` publishes `JobAttemptEvent` --> `backend-job` via `KAFKA_JOB_ATTEMPT_FAST_TOPIC` or `KAFKA_JOB_ATTEMPT_SLOW_TOPIC`
- `backend-job` publishes `JobInitCompletionEvent` to `backend-api` via `KAFKA_JOB_INIT_COMPLETION_TOPIC`
- `backend-job` publishes `JobAttemptCompletionEvent` to `backend-api` via `KAFKA_JOB_ATTEMPT_COMPLETION_TOPIC` (for both fast and slow attempts)

### Job Event Specs

- `JobInitEvent`

```
{
    "challenge_id": 3,
    "challenge_name": "Fabian Pascal",
    "init": "<CREATE DATABASE...>",
    "expires_at": "2022-06-01T12:00:00+00:00",
    "solution": "<SELECT ...>",
    "times_to_run": 10,
    "test_cases": [
        {
            "id": 1,
            "data": "<INSERT ...>"
        },
        {
            "id": 2,
            "data": "<INSERT ...>"
        }
    ],
}
```

- `JobAttemptEvent`

```
{
    "attempt_id": 1,
    "user_id": 2,
    "challenge_id": 3,
    "challenge_name": "Fabian Pascal",
    "query": "<SELECT ...>"
}
```

- `JobInitCompletionEvent`

```
{
    "challenge_id": 3,
    "status": "COMPLETED", //or 'FAILED'
    "error": "Some error message" //optional
}
```

- `JobAttemptCompletionEvent`

```
{
    "attempt_id": 1,
    "user_id": 2,
    "challenge_id": 3,
    "test_case_id": 2,
    "status": "COMPLETED", //or 'FAILED'
    "execution_ms": 100,
    "expected_result": "", //JSON serialized string
    "actual_result": "", //JSON serialized string
    "error": "Some error message" //optional
}
```