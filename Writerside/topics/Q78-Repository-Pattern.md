# Q78) Repository 패턴

Repository 패턴은 **데이터 접근 로직을 도메인 계층 뒤로 숨기는 추상화 계층**입니다. ViewModel이나 UseCase는 "데이터를 어디서, 어떻게 가져오는지"를 알 필요 없이, Repository가 제공하는 인터페이스에만 의존합니다. 네트워크 API, 로컬 DB, 메모리 캐시 같은 구체적인 데이터 출처(데이터소스)는 Repository 내부에 캡슐화됩니다.

안드로이드 권장 아키텍처에서 Repository는 **데이터 계층(data layer)의 공개 진입점**입니다. 이 토픽에서는 Repository가 어떤 책임을 갖는지를 네 가지 축으로 나눠 봅니다: 인터페이스 분리, DTO↔Domain 매핑, 데이터소스 통합, 그리고 SSOT(단일 진실 공급원)입니다.

## 인터페이스 분리 {#interface-segregation}

Repository는 **인터페이스(추상)와 구현(구체)을 분리**해 정의하는 것이 표준입니다. 도메인 계층에는 `interface`를, 데이터 계층에는 그 구현 클래스를 둡니다.

```kotlin
// domain 계층: 무엇을 할 수 있는지만 선언
interface UserRepository {
    suspend fun getUser(id: String): User
    fun observeUser(id: String): Flow<User>
}

// data 계층: 어떻게 하는지를 구현
class DefaultUserRepository(
    private val remote: UserRemoteDataSource,
    private val local: UserLocalDataSource,
) : UserRepository { /* ... */ }
```

### 왜 분리하는가 {#why-segregate}

분리의 이유는 **의존성 방향을 뒤집기 위해서**입니다. ViewModel은 `interface UserRepository`에만 의존하고, 구체 클래스 `DefaultUserRepository`는 모릅니다. 이로써 세 가지가 가능해집니다.

1. **테스트 용이성**: 테스트에서 `FakeUserRepository`를 주입해, 실제 네트워크 없이 ViewModel 로직만 검증할 수 있습니다.
2. **구현 교체**: Retrofit을 Ktor로 바꾸거나 DB를 교체해도, 인터페이스가 같으면 상위 계층 코드는 손대지 않습니다.
3. **컴파일 의존성 격리**: 도메인 모듈이 데이터 구현 모듈(네트워크 라이브러리 등)에 컴파일타임으로 의존하지 않습니다.

Hilt에서는 인터페이스와 구현을 `@Binds`로 연결합니다.

```kotlin
@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {
    @Binds
    abstract fun bindUserRepository(
        impl: DefaultUserRepository,
    ): UserRepository
}
```

이 패턴을 과하게 적용하지는 않습니다. 구현이 하나뿐이고 교체·테스트 더블이 필요 없는 단순 케이스라면 인터페이스 없이 구체 클래스만 두는 선택도 정당합니다. 분리는 비용(클래스·바인딩 증가)을 동반하므로, 위 세 가지 이점이 실제로 필요할 때 적용합니다.

## DTO와 Domain 모델 매핑 {#dto-domain-mapping}

Repository의 핵심 책임 하나는 **외부 데이터 표현(DTO)을 내부 도메인 모델로 변환**하는 것입니다.

- **DTO(Data Transfer Object)**: 네트워크 응답·DB 행처럼 **외부 시스템의 형태를 그대로 반영한 모델**입니다. JSON 키 이름, nullable 필드, 직렬화 애너테이션 등 외부 사정에 묶입니다.
- **Domain 모델**: 앱이 **실제로 다루고 싶은 형태**입니다. 직렬화와 무관하고, 필드는 의미 단위로 정제되어 있습니다.

```kotlin
// DTO — 서버 JSON 구조에 종속
data class UserDto(
    @SerializedName("user_id") val userId: String?,
    @SerializedName("display_name") val displayName: String?,
    @SerializedName("avatar_url") val avatarUrl: String?,
)

// Domain — 앱 내부에서 다루는 형태
data class User(
    val id: String,
    val name: String,
    val avatarUrl: String?,
)

// 매핑은 Repository(또는 전용 Mapper)의 책임
fun UserDto.toDomain(): User = User(
    id = userId ?: error("user_id is required"),
    name = displayName.orEmpty(),
    avatarUrl = avatarUrl,
)
```

### 왜 분리하는가 {#why-map}

매핑을 두는 이유는 **외부 변화로부터 도메인을 보호**하기 위해서입니다.

1. **변경 격리**: 서버 JSON 필드명이 바뀌면 `UserDto`와 매핑 함수만 고치면 됩니다. `User`를 쓰는 ViewModel·UI 코드는 그대로입니다.
2. **불변식 보장**: DTO의 nullable·낙관적 필드를 매핑 시점에 검증·기본값 처리해, 도메인 모델은 항상 유효한 상태(예: `id`는 non-null)로 만듭니다.
3. **관심사 분리**: UI 계층이 `@SerializedName` 같은 직렬화 세부사항을 모르게 합니다.

네트워크 DTO와 DB 엔티티가 따로 있는 경우, Repository는 보통 두 종류 모두를 같은 Domain 모델로 매핑합니다. 매핑 로직이 커지면 별도 `Mapper` 클래스로 분리해 Repository를 얇게 유지합니다.

## 여러 데이터소스 통합 {#datasource-coordination}

Repository는 **여러 데이터소스를 조율(coordinate)해 하나의 일관된 데이터 흐름**으로 합칩니다. 흔한 전략은 로컬 캐시를 우선 노출하고 원격으로 갱신하는 **offline-first**입니다.

```kotlin
class DefaultUserRepository(
    private val remote: UserRemoteDataSource,  // Retrofit API
    private val local: UserLocalDataSource,    // Room DAO
) : UserRepository {

    // DB를 구독해 화면에 흘려보낸다 (로컬이 노출 출처)
    override fun observeUser(id: String): Flow<User> =
        local.observe(id).map { it.toDomain() }

    // 네트워크에서 받아 DB에 쓴다. 화면 갱신은 위 Flow가 자동으로 처리
    override suspend fun refreshUser(id: String) {
        val dto = remote.fetchUser(id)
        local.upsert(dto.toEntity())
    }
}
```

여기서 핵심 메커니즘은 **읽기 경로와 쓰기 경로의 분리**입니다.

- **읽기**: UI는 `observeUser()`(로컬 DB Flow)만 구독합니다. 네트워크를 직접 보지 않습니다.
- **쓰기**: `refreshUser()`가 네트워크 결과를 DB에 반영하면, DB Flow가 변경을 감지해 UI로 새 값을 흘려보냅니다.

이 구조의 이점은 **네트워크 응답과 화면 갱신이 직접 결합되지 않는다**는 것입니다. 데이터 변경은 항상 "DB에 쓴다 → DB가 통지한다" 한 경로로만 일어나므로, 어디서 갱신을 트리거하든 화면은 동일한 출처에서 갱신됩니다. 이 성질이 다음 절의 SSOT로 이어집니다.

## SSOT: 단일 진실 공급원 {#single-source-of-truth}

SSOT(Single Source Of Truth)는 **특정 데이터에 대해 "진짜 값"을 보유하는 출처를 단 하나로 정한다**는 원칙입니다. 모든 읽기와 쓰기는 그 출처를 거칩니다.

위 예시에서 SSOT는 **로컬 DB(Room)** 입니다. 네트워크는 DB를 갱신하는 입력일 뿐, 화면이 직접 구독하는 대상이 아닙니다.

### 왜 SSOT가 필요한가 {#why-ssot}

SSOT가 없으면 같은 데이터의 사본이 여러 곳(메모리 변수, 화면 A, 화면 B, 네트워크 응답)에 흩어지고, 일부만 갱신되어 **불일치**가 생깁니다. 단일 출처를 정하면 다음이 보장됩니다.

1. **일관성**: 어떤 화면이든 같은 출처를 구독하므로, 데이터가 바뀌면 모든 구독자가 동일한 값을 받습니다.
2. **갱신 경로 단순화**: "데이터를 바꾼다"는 항상 "SSOT에 쓴다" 하나로 통일됩니다. 변경을 여러 곳에 직접 반영할 필요가 없습니다.
3. **오프라인 동작**: DB가 출처이므로 네트워크가 끊겨도 마지막으로 저장된 값을 그대로 노출할 수 있습니다.

> SSOT가 반드시 DB일 필요는 없습니다. 서버에 매번 묻는 것이 옳은 데이터(예: 결제 잔액)라면 네트워크가 SSOT가 될 수도 있고, 휘발성 상태는 메모리 캐시가 SSOT가 될 수도 있습니다. 중요한 것은 **출처를 하나로 정하고 모두가 그것을 거치게 하는 것**이지, 그 출처가 무엇이냐가 아닙니다.

Repository 패턴과 SSOT는 함께 동작합니다. Repository가 데이터 계층의 단일 진입점이기 때문에, "어디를 SSOT로 둘지"를 결정하고 강제할 수 있는 자리도 Repository입니다.

## 요약 {#summary}

> **TL;DR** — Repository는 데이터 계층의 단일 진입점으로, 데이터 출처를 도메인 뒤에 숨깁니다. 인터페이스와 구현을 분리해 테스트·교체를 쉽게 하고, DTO를 Domain 모델로 매핑해 외부 변화로부터 앱을 보호하며, 여러 데이터소스를 조율해 하나의 흐름으로 합치고, 그 흐름의 진짜 값을 보유하는 출처(SSOT)를 하나로 정해 데이터 일관성을 보장합니다.

1. **인터페이스 분리**: 도메인에 `interface`, 데이터 계층에 구현을 둬 의존성 방향을 뒤집는다 — 테스트 더블 주입, 구현 교체, 컴파일 의존성 격리가 가능해진다.
2. **DTO↔Domain 매핑**: 외부 형태(DTO)를 내부 형태(Domain)로 변환해, 서버·DB 스키마 변경의 영향을 매핑 지점에 가두고 도메인 모델의 불변식을 보장한다.
3. **데이터소스 통합**: 네트워크·로컬 DB 등 여러 출처를 Repository가 조율한다. 읽기는 로컬 Flow를 구독하고, 쓰기는 네트워크 결과를 로컬에 반영하는 식으로 경로를 분리한다.
4. **SSOT**: 특정 데이터의 진짜 값을 보유하는 출처를 하나로 정해, 모든 읽기·쓰기를 그곳으로 통일한다 — 일관성, 단순한 갱신 경로, 오프라인 동작을 얻는다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Repository 패턴이 무엇이고, 어떤 문제를 해결하나요?">

Repository 패턴은 데이터 접근 로직을 도메인 계층 뒤로 숨기는 추상화 계층입니다. ViewModel·UseCase는 데이터가 어디서 어떻게 오는지 모른 채 Repository 인터페이스에만 의존하고, 네트워크·로컬 DB·캐시 같은 구체 출처는 Repository 내부에 캡슐화됩니다.

이로써 데이터 접근 관심사가 한 곳에 모입니다. 상위 계층은 데이터 출처 변경(예: API 교체, 캐시 추가)의 영향을 받지 않고, 데이터 계층은 출처 통합·매핑·캐싱 정책 같은 책임을 한 자리에서 관리할 수 있습니다. 안드로이드 권장 아키텍처에서 Repository는 데이터 계층의 공개 진입점 역할을 합니다.

</def>
<def title="Q) Repository 인터페이스와 구현을 분리하는 이유는 무엇인가요?">

의존성 방향을 뒤집기 위해서입니다. 도메인 계층에 `interface`를 두고 데이터 계층에 구현을 두면, ViewModel은 인터페이스에만 의존하고 구체 클래스는 모릅니다.

이로써 세 가지가 가능해집니다. 첫째, 테스트에서 가짜 구현(Fake)을 주입해 실제 네트워크 없이 상위 로직만 검증할 수 있습니다. 둘째, Retrofit을 Ktor로 바꾸는 식으로 구현을 교체해도 인터페이스가 같으면 상위 코드는 그대로입니다. 셋째, 도메인 모듈이 데이터 구현 모듈(네트워크 라이브러리 등)에 컴파일타임으로 의존하지 않습니다. Hilt에서는 `@Binds`로 인터페이스와 구현을 연결합니다. 다만 구현이 하나뿐이고 교체·테스트 더블이 불필요하다면 인터페이스 없이 구체 클래스만 두는 선택도 정당합니다.

</def>
<def title="Q) DTO와 Domain 모델을 굳이 나누고 매핑하는 이유는 무엇인가요?">

외부 데이터 표현의 변화로부터 도메인을 보호하기 위해서입니다. DTO는 서버 JSON·DB 행처럼 외부 시스템의 형태를 그대로 반영한 모델이라 직렬화 애너테이션, nullable 필드 등 외부 사정에 묶입니다. Domain 모델은 앱이 실제로 다루고 싶은 정제된 형태입니다.

매핑을 두면 서버 필드명이 바뀌어도 DTO와 매핑 함수만 고치면 되고, 도메인 모델을 쓰는 UI·ViewModel 코드는 그대로입니다. 또 매핑 시점에 nullable·낙관적 필드를 검증·기본값 처리해 도메인 모델이 항상 유효한 상태(예: id는 non-null)가 되도록 보장할 수 있습니다. UI 계층이 `@SerializedName` 같은 직렬화 세부사항을 모르게 한다는 관심사 분리 효과도 있습니다.

</def>
<def title="Q) Repository는 여러 데이터소스(네트워크 + 로컬 DB)를 어떻게 조율하나요?">

offline-first 전략이 대표적입니다. 읽기 경로와 쓰기 경로를 분리하는 것이 핵심입니다. UI는 로컬 DB의 Flow(`observeUser()`)만 구독하고 네트워크를 직접 보지 않습니다. 갱신이 필요하면 `refreshUser()`가 네트워크 결과를 받아 DB에 쓰고, DB Flow가 변경을 감지해 UI로 새 값을 흘려보냅니다.

이 구조의 이점은 네트워크 응답과 화면 갱신이 직접 결합되지 않는다는 것입니다. 데이터 변경은 항상 "DB에 쓴다 → DB가 통지한다"는 한 경로로만 일어나므로, 어디서 갱신을 트리거하든 화면은 동일한 출처에서 일관되게 갱신되고, 네트워크가 끊겨도 마지막 저장값을 노출할 수 있습니다.

</def>
<def title="Q) SSOT(단일 진실 공급원)란 무엇이고, Repository와 어떻게 연결되나요?">

SSOT는 특정 데이터에 대해 진짜 값을 보유하는 출처를 단 하나로 정하고, 모든 읽기·쓰기가 그 출처를 거치게 하는 원칙입니다. offline-first 구성에서는 보통 로컬 DB가 SSOT이고, 네트워크는 DB를 갱신하는 입력일 뿐 화면이 직접 구독하는 대상이 아닙니다.

SSOT가 없으면 같은 데이터의 사본이 여러 화면·변수에 흩어져 일부만 갱신되며 불일치가 생깁니다. 출처를 하나로 정하면 모든 구독자가 같은 값을 받아 일관성이 보장되고, "데이터를 바꾼다"가 "SSOT에 쓴다" 하나로 단순화되며, DB가 출처이면 오프라인에서도 동작합니다. SSOT가 반드시 DB일 필요는 없고(잔액처럼 항상 서버가 옳으면 네트워크가 SSOT일 수 있음), 중요한 것은 출처를 하나로 정하는 것입니다. Repository는 데이터 계층의 단일 진입점이므로 어디를 SSOT로 둘지 결정하고 강제하는 자리가 됩니다.

</def>
</deflist>
