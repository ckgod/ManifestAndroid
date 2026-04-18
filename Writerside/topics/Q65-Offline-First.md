# Q65) Offline-first 기능

## Offline-first 기능은 어떻게 다루나요? {#how-to-handle-offline-first}

Offline-first 디자인은 활성 네트워크 연결 없이도 애플리케이션이 매끄럽게 동작할 수 있도록 만드는 접근 방식입니다. 로컬에 캐시되거나 저장된 데이터에 의존해 화면을 그리고, 연결이 회복되었을 때 원격 서버와 동기화하는 흐름이 그 핵심입니다. 네트워크 환경이 좋지 않거나 간헐적인 연결이 잦은 환경에서 특히 사용자 경험이 크게 개선됩니다. Android 공식 문서의 [offline-first 가이드](https://developer.android.com/topic/architecture/data-layer/offline-first)에서 권장 패턴을 자세히 확인할 수 있습니다.

### Offline-first 아키텍처의 핵심 개념 {#key-concepts}

#### 1. 로컬 데이터 영속성 {#local-data-persistence}

신뢰할 수 있는 offline-first 전략은 결국 견고한 로컬 저장에서 시작합니다. Jetpack의 일부인 **Room Database** 가 구조화된 로컬 데이터를 다루는 권장 솔루션입니다. Room을 사용하면 오프라인 상태에서도 데이터를 읽고 쓸 수 있고, Kotlin Coroutines·Flow·LiveData와 자연스럽게 결합되어 UI에 변경 사항을 반응형으로 전달할 수 있습니다.

#### 2. 데이터 동기화 {#data-synchronization}

로컬 데이터와 원격 데이터의 일관성을 유지하려면 동기화 메커니즘이 필요합니다. **WorkManager** 가 이 역할을 맡기에 좋은 선택입니다. 네트워크 연결과 같은 조건이 충족되었을 때만 실행되도록 동기화 작업을 지연시킬 수 있고, 실패한 작업은 자동으로 재시도되므로 데이터 무결성을 유지하기에 적합합니다.

#### 3. 캐시·페치 정책 {#cache-and-fetch-policies}

데이터를 어떻게 캐시하고 가져올지에 대한 명확한 정책이 필요합니다. 예를 들면 다음과 같습니다.

- **Read-through caching**: 앱이 로컬 저장소를 먼저 조회하고, 필요한 경우에만 네트워크를 호출합니다.
- **Write-through caching**: 변경 사항을 로컬에 먼저 기록하고, 백그라운드에서 서버와 동기화합니다.

#### 4. 충돌 해결 {#conflict-resolution}

로컬과 원격 사이에 데이터를 동기화할 때는 충돌 해결 전략을 함께 정의해야 합니다.

- **Last-write-wins**: 가장 최근의 변경을 우선시합니다.
- **커스텀 로직**: 사용자가 직접 충돌을 해결하게 하거나, 도메인 규칙을 적용하는 방식입니다.

### 실전 구현 예시 {#practical-implementation}

다음은 Room과 WorkManager를 함께 사용해 offline-first 기능을 구현하는 예시입니다.

```kotlin
@Entity
data class Article(
    @PrimaryKey val id: Int,
    val title: String,
    val content: String,
    val isSynced: Boolean = false
)

@Dao
interface ArticleDao {
    @Query("SELECT * FROM Article")
    fun getAllArticles(): Flow<List<Article>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertArticle(article: Article)
}

class SyncWorker(
    appContext: Context,
    params: WorkerParameters
) : CoroutineWorker(appContext, params) {

    override suspend fun doWork(): Result {
        val articleDao = AppDatabase.getInstance(applicationContext).articleDao()
        val unsyncedArticles = articleDao.getAllArticles()
            .firstOrNull()
            ?.filter { !it.isSynced }
            ?: return Result.success()

        if (syncToServer(unsyncedArticles)) {
            unsyncedArticles.forEach {
                articleDao.insertArticle(it.copy(isSynced = true))
            }
        }

        return Result.success()
    }

    private suspend fun syncToServer(articles: List<Article>): Boolean {
        // 동기화 로직 (예시)
        return true
    }
}
```
{title="OfflineFirstFeature.kt"}

이렇게 만들어 둔 `SyncWorker`는 동기화 전략에 맞춰 실행 시점을 정할 수 있습니다. 예를 들어 모든 타임라인 데이터를 동기화해야 한다면 사용자가 앱을 실행할 때 Jetpack의 App Startup을 활용해 단 한 번만 트리거할 수도 있습니다. 실제 구현 사례는 GitHub의 [SyncWorker.kt](https://github.com/advocacies/nowinandroid_/blob/d42262c9391ccd1d59a0c92476c2b349a5acc3af/sync/work/src/main/kotlin/com/google/samples/apps/nowinandroid/sync/workers/SyncWorker.kt#L51)와 [SyncInitializer.kt](https://github.com/advocacies/nowinandroid_/blob/d42262c9391ccd1d59a0c92476c2b349a5acc3af/sync/work/src/main/kotlin/com/google/samples/apps/nowinandroid/sync/initializers/SyncInitializer.kt#L23)를 참고하면 좋습니다.

### 정리 {#recap}

1. 백그라운드 동기화는 **WorkManager** 로 관리합니다.
2. 견고한 로컬 저장은 **Room** 으로 구성합니다.
3. 효율적인 데이터 가져오기를 위해 **명확한 캐시 정책** 을 정의합니다.
4. 일관성을 보장하기 위해 **충돌 해결 메커니즘** 을 함께 설계합니다.

### 요약 {#summary}

<tldr>

Android에서 offline-first 접근은 연결 상태와 무관하게 매끄럽게 동작하는 앱을 만들기 위한 전략입니다. Room, WorkManager, 적절한 캐싱 전략을 함께 활용하면 사용자에게 일관된 경험을 제공할 수 있습니다. 더 깊이 있는 가이드는 [공식 문서](https://developer.android.com/topic/architecture/data-layer/offline-first)에서 확인할 수 있습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 네트워크가 사용 불가능한 상황에서도 자연스러운 사용자 경험을 보장하기 위해 Android 앱의 offline-first 기능을 어떻게 설계하시겠습니까?">

핵심은 UI가 항상 **로컬 데이터** 를 단일 진실의 원천(single source of truth)으로 삼도록 만드는 것입니다. 네트워크에서 받아 온 데이터는 항상 Room 같은 로컬 저장소를 거쳐 UI로 흘러가도록 단방향 흐름을 구성합니다. 이렇게 하면 온라인일 때도, 오프라인일 때도 UI 코드가 동일하게 동작하고, "데이터가 없을 때만 보여주는 분기" 같은 복잡한 조건문이 줄어듭니다.

데이터 변경은 두 갈래로 처리합니다. 사용자가 만든 변경(예: 글 작성, 좋아요)은 먼저 로컬에 즉시 반영하고, 동기화 상태를 표시하는 플래그(예: `isSynced`)를 함께 저장합니다. 네트워크 연결이 가능해지는 시점에 WorkManager로 등록된 동기화 워커가 깨어나, 동기화되지 않은 항목들을 서버로 보내고 응답을 반영합니다. 이 패턴 덕분에 사용자는 비행 모드에서도 끊김 없이 앱을 쓸 수 있고, 네트워크가 회복되면 변경 사항이 자동으로 서버까지 전파됩니다.

화면 단에서는 "마지막 동기화 시각"이나 "동기화 대기 중" 같은 작은 상태 표시를 통해, 지금 보이는 데이터가 캐시 기반인지 최신인지를 사용자에게 부드럽게 알려 주는 것이 좋습니다. 이런 작은 신호가 오프라인 상태에서도 사용자가 앱을 신뢰하고 계속 사용할 수 있도록 만들어 줍니다.

</def>
<def title="Q) 로컬 Room 데이터베이스의 변경 사항을 원격 서버와 동기화하기 위해 어떤 전략을 쓰며, 로컬과 원격이 모두 변경된 경우의 충돌은 어떻게 해결하시겠습니까?">

기본 전략은 **로컬에 변경 시각과 동기화 상태를 함께 저장하는 것** 에서 시작합니다. 각 엔티티에 `updatedAt`이나 `version` 같은 필드와 `isSynced` 같은 플래그를 두면, 어떤 항목이 어느 시점에 어디서 변경되었는지를 추적할 수 있습니다. 동기화 워커는 `isSynced = false`인 항목을 모아 서버로 보내고, 성공한 항목은 `isSynced = true`로 갱신합니다. 반대로 서버에서 변경된 데이터를 받아 올 때도 같은 시각 기준으로 로컬에 반영합니다.

충돌 해결 정책은 도메인 성격에 따라 갈립니다. 가장 단순한 방식은 **last-write-wins**, 즉 `updatedAt`을 비교해 더 최근의 변경을 채택하는 것입니다. 사용자 한 명이 여러 디바이스를 오가는 가벼운 메모 앱 같은 경우에는 보통 이 정책으로 충분합니다. 하지만 협업 도구나 결제처럼 잘못된 덮어쓰기가 치명적인 도메인이라면, **버전 기반 충돌 감지** 와 **사용자 주도 머지** 가 필요합니다. 서버가 응답으로 충돌을 알려 주면, 클라이언트는 양쪽 버전을 보여 주고 사용자가 선택하거나 수동으로 합칠 수 있도록 UX를 제공합니다.

또 하나 중요한 부분은 **부분 실패에 대한 견고성** 입니다. WorkManager의 재시도 정책과 지수 백오프를 활용해 일시적 실패를 자동으로 회복시키고, 영속적인 실패는 사용자에게 알린 뒤 다시 시도할 수 있도록 만들어야 합니다. 동기화 흐름은 한 번에 하나만 실행되도록 unique work 이름을 부여해 두는 것이 좋습니다. 그렇지 않으면 동시에 실행된 두 워커가 같은 항목을 중복 동기화해 정합성이 깨질 수 있습니다.

</def>
</deflist>
