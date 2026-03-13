# 🚀 EC2 → ECS(Fargate) 이전 가이드: 초보자를 위한 딥다이브

이 가이드는 단순한 절차 요약을 넘어, 각 단계에서 어떤 버튼을 눌러야 하는지, 왜 그렇게 설정해야 하는지에 대한 **심층적인 기술 정보**를 담고 있습니다.

---

## 🏗️ 1. 네트워크 기반 (VPC & 보안)

모든 인프라의 시작은 **VPC(Virtual Private Cloud)**입니다. 전용 통신망을 제대로 구축해야 RDS와 컨테이너가 막힘없이 대화할 수 있습니다.

### [Phase 0] VPC 구축 상세
- **메뉴**: VPC 콘솔 -> [VPC 및 기타 (VPC and more)] 선택
- **주요 설정**:
    - **가용 영역(AZ)**: `2개` (ap-northeast-2a, 2c 권장)
    - **서브넷**: `퍼블릭 서브넷 2개`, `프라이빗 서브넷 0개`
        - *주의: NAT 게이트웨이는 비용이 많이 발생하므로, 초보 단계에서는 퍼블릭 서브넷 위에 리소스를 올리는 것이 경제적입니다.*
- **보안 그룹(Security Group) 설정**:
    - **`alb-sg` (길목)**: 포트 80(HTTP), 8000(Django)을 `0.0.0.0/0`에서 허용.
    - **`rds-sg` (금고)**: 포트 5432(PostgreSQL)를 허용하되, 소스를 `alb-sg` 보안 그룹 ID로 지정 (보안 강화).

---

## 💾 2. 데이터베이스 (RDS)

컨테이너 환경에서 SQLite는 금기입니다. 컨테이너가 꺼지면 데이터가 사라지기 때문입니다.

### [Phase 1] RDS 구축 상세
- **엔진**: PostgreSQL (버전 15 이상 추천)
- **템플릿**: `프리 티어` (비용 발생 방지)
- **인스턴스 설정**: `db.t3.micro` 또는 `db.t4g.micro`
- **연결성**: 
    - **VPC**: 위에서 만든 `practice-vpc` 선택
    - **퍼블릭 액세스**: `아니요` (로드 밸런서를 통해서만 내부 통신)
    - **DB 서브넷 그룹**: 반드시 2개 이상의 AZ를 포함하는 서브넷 그룹 사용.
- **데이터베이스 옵션**: 초기 데이터베이스 이름(예: `hari1-db`)을 명시적으로 입력해줘야 서비스 시작 시 테이블이 생성됩니다.

---

## 📦 3. 이미지 저장소 (ECR)

우리가 만든 코드를 도커 이미지로 구워 보관할 창고입니다.

### [Phase 2] ECR 구축 상세
- **가시성**: `Private` (코드가 유출되지 않도록 설정)
- **이름**: `hari-backend`
- **URI 보관**: 생성 후 나타나는 `939213667098.dkr.ecr.ap-northeast-2.amazonaws.com/hari-backend` 주소는 배포 스크립트의 핵심이 됩니다.

---

## 🚢 4. 컨테이너 실행 환경 (ECS & ALB)

여기부터가 진짜 ECS의 핵심입니다. '설계도'를 만들고 '엔진'을 돌립니다.

### [Phase 3-1] 로드 밸런서(ALB) 상세
- **유형**: Application Load Balancer
- **접속 방식**: 인터넷 페이싱(Internet-facing)
- **네트워크 매핑**: VPC 내의 모든 퍼블릭 서브넷 선택.
- **대상 그룹(Target Group) 생성 시 주의사항**:
    - **Target type**: 반드시 **`IP`** 선택 (Fargate는 인스턴스가 아닌 IP로 통신함).
    - **Port**: `8000` (장고 포트).
    - **Health Check**: 경로 `/`에 대해 200번 응답이 오는지 확인.

### [Phase 3-2] 태스크 정의(Task Definition)
- **Launch Type**: `FARGATE`
- **운영 체제**: `Linux`
- **CPU/메모리**: `0.25 vCPU / 0.5 GB` (최소 사양) 또는 `0.5 vCPU / 1 GB` (추천)
- **컨테이너 추가**:
    - **이미지**: ECR 주소 입력.
    - **포트 매핑**: 컨테이너 포트 `8000`.
    - **환경변수**: `DB_HOST`, `DB_NAME`, `DB_USER` 등을 상수로 넣거나 Secrets Manager에서 연동.

---

## ⚙️ 5. 자동 자동화 (CI/CD)

GitHub에 소스를 올리는 것만으로 배포가 끝나는 과정입니다.

### [Phase 4] GitHub Actions & Secrets 상세
- **파일 경로**: `.github/workflows/deploy-ecs.yml`
- **작동 원리**: 
    1. GitHub 서버가 소스를 가져옴 -> 2. 도커 이미지 빌드 -> 3. ECR로 Push -> 4. ECS 작업 정의 개정(Revision) 생성 -> 5. ECS 서비스 업데이트.
- **필수 Secrets**:
    - `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`: 배포 권한.
    - `DB_PASSWORD`: RDS 암호.
    - `DJANGO_SECRET_KEY`: 장고 보안 키.
    - `OPENAI_API_KEY`: 앱 기능용 키.

---

## 🆘 6. 트러블슈팅 Quick Guide

1.  **배포 중 서비스가 계속 'Starting'인 경우**:
    - 원인: 보안 그룹에서 8000번 포트가 막혔거나, RDS 주소가 틀렸을 확률이 90%입니다.
    - 해결: ECS의 '중단된 태스크' 탭에서 에러 로그(Log)를 확인하세요.
2.  **`ecsTaskExecutionRole` 에러**:
    - 원인: ECS가 로그를 쓰거나 이미지를 가져올 권한이 없는 '역할'을 사용 중입니다.
    - 해결: IAM에서 역할을 생성하고 `AmazonECSTaskExecutionRolePolicy` 정책을 연결해야 합니다.
3.  **데이터베이스 연결 에러 (timeout)**:
    - 원인: RDS 보안 그룹에서 포트 5432가 열려있지 않습니다.
    - 해결: RDS 인바운드 규칙에 ECS 보안 그룹을 등록하세요.

---

> [!IMPORTANT]
> **성공 여부 확인**: 로드 밸런서의 **DNS 이름**으로 접속했을 때 우리 프로젝트의 첫 화면이 나오면 성공입니다! (예: `http://hari-alb-xxxx.ap-northeast-2.elb.amazonaws.com`)
