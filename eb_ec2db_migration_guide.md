# AWS Elastic Beanstalk & EC2 데이터베이스 마이그레이션 가이드

이 가이드는 ECS 및 RDS에서 벗어나, **Elastic Beanstalk (EB)**와 독립형 **EC2** 인스턴스에 직접 설치한 PostgreSQL 데이터베이스를 사용하는 아키텍처로 전환하는 방법을 다룹니다.

---

## 🏗️ 1단계: 데이터베이스 구축 (EC2)

관리형 서비스인 RDS 대신, EC2 인스턴스에 PostgreSQL을 직접 설치하여 운영합니다.

### 1. 데이터베이스 EC2 인스턴스 시작
1. **AWS 콘솔 > EC2 > 인스턴스 > 인스턴스 시작**으로 이동합니다.
2. **이름**: `myapp-db-instance`
3. **AMI**: Ubuntu Server 24.04 LTS (HVM), SSD Volume Type 선택.
4. **인스턴스 유형**: `t2.micro` 또는 `t3.micro`.
5. **키 페어**: 기존 키 페어를 선택하거나 새로 생성합니다.
6. **네트워크 설정**:
   - **VPC / 서브넷**: 기본 VPC와 사용 가능한 퍼블릭 서브넷을 선택합니다.
   - **퍼블릭 IP 자동 할당**: 활성화(Enable).
   - **보안 그룹**: `DB-SG`라는 이름으로 새 보안 그룹을 생성합니다.
     - **SSH (22)**: `내 IP` 또는 `위치 무관(Anywhere)` 허용.
     - **사용자 지정 TCP (5432)**: `위치 무관` 허용 (나중에 VPC 대역으로 제한 가능).
7. 인스턴스를 시작합니다.

### 2. PostgreSQL 설치 및 설정
1. 인스턴스에 SSH로 접속합니다:
   ```bash
   ssh -i /path/to/key.pem ubuntu@<EC2_PUBLIC_IP>
   ```
2. 패키지 업데이트 및 Postgres 설치:
   ```bash
   sudo apt update
   sudo apt install postgresql postgresql-contrib -y
   ```
3. 데이터베이스 사용자 및 DB 생성:
   ```bash
   sudo -i -u postgres
   psql
   ```
   *psql 프롬프트 내에서:*
   ```sql
   CREATE DATABASE myapp_db;
   CREATE USER myapp_user WITH PASSWORD 'securepassword123';
   ALTER ROLE myapp_user SET client_encoding TO 'utf8';
   ALTER ROLE myapp_user SET default_transaction_isolation TO 'read committed';
   ALTER ROLE myapp_user SET timezone TO 'UTC';
   GRANT ALL PRIVILEGES ON DATABASE myapp_db TO myapp_user;
   \q
   ```
   ```bash
   exit
   ```

### 3. 외부 접속 허용 설정
1. `postgresql.conf` 수정:
   ```bash
   sudo nano /etc/postgresql/16/main/postgresql.conf
   ```
   *`listen_addresses` 항목을 찾아 다음과 같이 변경합니다:*
   ```ini
   listen_addresses = '*'
   ```
2. `pg_hba.conf` 수정:
   ```bash
   sudo nano /etc/postgresql/16/main/pg_hba.conf
   ```
   *파일 맨 아래에 다음 내용을 추가합니다:*
   ```text
   host    all             all             0.0.0.0/0               md5
   ```
3. PostgreSQL 재시작:
   ```bash
   sudo systemctl restart postgresql
   ```

*이 EC2 인스턴스의 **프라이빗 IP**와 퍼블릭 IP를 메모해 두세요. 프라이빗 IP를 `DB_HOST`로 사용하게 됩니다.*

---

## 🚀 2단계: Elastic Beanstalk 환경 생성

Elastic Beanstalk는 배포를 단순화해줍니다. 우리는 `docker-compose.yml`을 그대로 인식하는 **Docker** 플랫폼을 사용합니다.

### 1. 애플리케이션 및 환경 생성
1. **AWS 콘솔 > Elastic Beanstalk > 애플리케이션 생성**으로 이동합니다.
2. **애플리케이션 이름**: `aws-practice`
3. **플랫폼**:
   - 플랫폼 유형: `Docker`
   - 플랫폼 브랜치: `Docker running on 64bit Amazon Linux 2023`
   - 플랫폼 버전: 권장 버전 선택.
4. **애플리케이션 코드**: `샘플 애플리케이션` (나중에 GitHub Actions로 배포할 예정).
5. **다음(Next)**을 클릭하여 구성을 진행합니다.

### 2. 서비스 액세스 구성
1. **서비스 역학(Service role)**: 기존 역할을 선택하거나 새 역할을 생성합니다.
2. **EC2 키 페어**: SSH 접속이 필요한 경우 기존 키 페어를 선택합니다.
3. **EC2 인스턴스 프로파일**: `aws-elasticbeanstalk-ec2-role`을 선택합니다. (없다면 IAM에서 생성 후 `AWSElasticBeanstalkWebTier` 등의 정책을 연결해야 합니다.)
4. **다음**을 클릭합니다.

### 3. 네트워킹, 데이터베이스 및 로드 밸런서 설정
1. **VPC**: 기본 VPC를 선택합니다.
2. **인스턴스 서브넷**: 사용 가능한 모든 퍼블릭 서브넷을 선택합니다.
3. **데이터베이스**: 이 부분은 건너뜁니다! (이미 EC2 DB를 직접 만들었습니다.)
4. **다음**을 클릭합니다.
5. **인스턴스 유형 및 보안 그룹**: 기본값을 유지하거나 `DB-SG` 접속 권한이 있는 보안 그룹을 선택합니다.
6. **다음**을 클릭하고, 상태 확인(Health) 설정은 일단 건너뜁니다.
7. **환경 유형**:
   - `단일 인스턴스`(Single instance): 저렴함, 테스트용.
   - `로드 밸런싱 수행`(Load balanced): 오토스케일링 가능, 운영용.
8. **다음**을 클릭합니다.

### 4. 환경 변수 설정
**업데이트, 모니터링 및 로깅** 섹션에서 아래로 스크롤하여 **환경 속성(Environment properties)**에 다음을 추가합니다:
- `DJANGO_SETTINGS_MODULE`: `config.settings`
- `DB_HOST`: `<EC2 데이터베이스의 프라이빗 IP>`
- `DB_NAME`: `myapp_db`
- `DB_USER`: `myapp_user`
- `DB_PASSWORD`: `securepassword123`
- `DB_PORT`: `5432`
- `DJANGO_SECRET_KEY`: `사용자의_장고_시크릿_키`
- `OPENAI_API_KEY`: `사용자의_API_키`

검토 후 **제출(Submit)**을 클릭하면 환경 구축이 시작됩니다 (약 5~10분 소요).

---

## ⚙️ 3단계: GitHub Actions 설정 (자동 배포)

인프라 준비가 끝나면:
1. `AWSElasticBeanstalkAdministrator` 권한이 있는 IAM 사용자의 액세스 키를 준비합니다.
2. GitHub 저장소의 **Settings > Secrets and variables > Actions**에 다음 항목을 추가합니다:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION` (예: `ap-northeast-2`)
   - `EB_APP_NAME`: `aws-practice`
   - `EB_ENV_NAME`: (생성한 환경 이름)

이제 `main` 브랜치에 코드를 푸시하면 GitHub Actions가 자동으로 프로젝트를 압축하여 Elastic Beanstalk로 배포합니다!
