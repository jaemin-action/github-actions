# Jira Data Dashboard

Jira 데이터를 시각화하는 웹 대시보드 애플리케이션입니다.

## 기능

- **대시보드**: 전체 이슈 현황, 상태별/우선순위별/담당자별 통계
- **이슈 목록**: JQL 쿼리를 통한 이슈 검색 및 필터링
- **프로젝트 관리**: 프로젝트별 이슈 현황 확인

## 기술 스택

- **Backend**: Python Flask
- **Frontend**: HTML, CSS, JavaScript
- **Charts**: Chart.js
- **API**: Jira REST API v3

## 설치 및 실행

### 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 Jira 정보를 입력하세요:

```bash
cp .env.example .env
```

필요한 환경 변수:
- `JIRA_BASE_URL`: Jira 인스턴스 URL (예: https://your-domain.atlassian.net)
- `JIRA_EMAIL`: Jira 계정 이메일
- `JIRA_API_TOKEN`: Jira API 토큰

> API 토큰은 [Atlassian 계정 설정](https://id.atlassian.com/manage-profile/security/api-tokens)에서 생성할 수 있습니다.

### Docker로 실행

```bash
docker-compose up -d
```

### 직접 실행

```bash
# 의존성 설치
cd backend
pip install -r requirements.txt

# 실행
python app.py
```

브라우저에서 `http://localhost:5000` 접속

## API 엔드포인트

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /api/config` | Jira 설정 확인 |
| `GET /api/projects` | 프로젝트 목록 |
| `GET /api/issues` | 이슈 목록 (JQL 지원) |
| `GET /api/issue/<key>` | 특정 이슈 상세 |
| `GET /api/dashboard/summary` | 대시보드 통계 |

## 스크린샷

### 대시보드
- 전체 이슈 수, 상태별 현황 카드
- 이슈 유형별/우선순위별/상태별 차트
- 담당자별 이슈 현황 테이블

### 이슈 목록
- JQL 쿼리 입력 지원
- 페이지네이션
- 상태/우선순위 배지

## 라이선스

MIT License
