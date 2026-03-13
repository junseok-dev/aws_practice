# AWS EC2에서 ECS(Fargate)로의 이전 가이드

이 가이드는 현재 EC2 기반의 단일 서버 환경을 AWS의 관리형 컨테이너 서비스인 **ECS (Elastic Container Service)** 환경으로 이전하기 위한 단계별 절차를 설명합니다.

---

## 1. 아키텍처 변화 이해

| 구분 | 현재 (EC2) | 변경 후 (ECS Fargate) |
| :--- | :--- | :--- |
| **운영 방식** | 가상 서버 직접 관리 (OS, Docker 설치 등) | 컨테이너 실행 리소스만 정의 (서버 관리 불필요) |
| **이미지 관리** | 서버 내부에서 `docker build` | **AWS ECR** 이미지 저장소 사용 |
| **데이터베이스** | 로컬 파일 (`SQLite`) | **AWS RDS** (PostgreSQL/MySQL) |
| **네트워킹** | 고정 IP (Elastic IP) | **Application Load Balancer (ALB)** |

---

## 2. 사전 준비 단계 (Pre-migration)

### ① 데이터베이스 이전 (가장 중요)
ECS Fargate는 "휘발성" 인스턴스입니다. 컨테이너가 재시작되면 내부의 SQLite 파일은 삭제됩니다.
*   **액션**: AWS RDS(PostgreSQL 추천) 인스턴스를 생성합니다.
*   **코드 변경**: `settings.py`의 `DATABASES` 설정을 SQLite에서 RDS 연결 정보로 변경합니다.

### ② AWS ECR 레포지토리 생성
이미지를 저장할 비공개 저장소(Registry)가 필요합니다.
*   **액션**: AWS 콘솔에서 `ECR` -> `Repositories` -> `Create repository` (이름: `aws-practice-backend`)

---

## 3. ECS 핵심 구성 요소 설정

### ① Task Definition (작업 정의)
하나의 세트를 어떻게 실행할지 정의하는 "설계도"입니다.
*   **Launch Type**: `FARGATE` 선택
*   **Operating System Family**: `Linux/X86_64`
*   **Task Size**: 0.5 vCPU / 1GB RAM (현재 t2.micro 사양과 유사)
*   **Container**: ECR 이미지 URL 입력 및 8000 포트 매핑
*   **Environment Variables**: `DJANGO_SECRET_KEY`, `RDS_HOSTNAME` 등 설정

### ② Cluster & Service 생성
*   **Cluster**: 논리적인 그룹입니다. (이름: `prod-cluster`)
*   **Service**: Task를 몇 개나 띄울지, 로드 밸런서와 어떻게 연결할지 관리합니다.
    *   **Desired tasks**: 1~2개
    *   **Load Balancing**: `Application Load Balancer` 선택

---

## 4. CI/CD 파이프라인 업데이트 (GitHub Actions)

기존의 SSH 방식 대신 AWS CLI를 사용하여 이미지를 밀어넣고 서비스를 업데이트하는 방식으로 변경해야 합니다.

```yaml
# .github/workflows/deploy-ecs.yml (예시 구조)
- name: Login to Amazon ECR
  uses: aws-actions/amazon-ecr-login@v2

- name: Build, tag, and push image to Amazon ECR
  env:
    ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
    IMAGE_TAG: ${{ github.sha }}
  run: |
    docker build -t $ECR_REGISTRY/aws-practice-backend:$IMAGE_TAG .
    docker push $ECR_REGISTRY/aws-practice-backend:$IMAGE_TAG

- name: Fill in the new image ID in the Amazon ECS task definition
  uses: aws-actions/amazon-ecs-render-task-definition@v1
  with:
    task-definition: task-definition.json
    container-name: backend
    image: ${{ steps.build-image.outputs.image }}

- name: Deploy Amazon ECS task definition
  uses: aws-actions/amazon-ecs-deploy-task-definition@v1
  with:
    task-definition: ${{ steps.task-def.outputs.task-definition }}
    service: backend-service
    cluster: prod-cluster
```

---

## 5. 단계별 이행 체크리스트

1. [ ] **코드 수정**: `db.sqlite3` 의존성 제거 및 RDS 연결 코드 적용
2. [ ] **비밀값 관리**: `Secrets Manager` 또는 ECS 환경변수에 민감 정보 등록
3. [ ] **보안 그룹(Security Group)**:
   *   RDS: ECS 컨테이너로부터의 5432(또는 3306) 포트 허용
   *   ALB: 외부(0.0.0.0/0)로부터의 80/443 포트 허용
4. [ ] **도메인 연결**: ALB DNS 주소를 가비아/Route53 등의 CNAME으로 등록

---

## 6. ECS 이전 시 얻는 이점
*   **고가용성**: 서버 한 대가 죽어도 AWS가 즉시 새 컨테이너를 띄워줍니다.
*   **무중단 배포**: 새로운 코드를 배포할 때 사용자는 끊김을 느끼지 못합니다.
*   **자유로운 확장**: 트래픽이 몰리면 순식간에 컨테이너 개수를 늘릴 수 있습니다.
