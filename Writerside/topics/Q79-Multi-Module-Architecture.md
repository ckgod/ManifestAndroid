# Q79) 멀티모듈 아키텍처

## 멀티모듈이란 무엇인가 {#what-is-multimodule}

멀티모듈 아키텍처란 하나의 앱 코드를 **여러 개의 Gradle 모듈로 쪼개어 구성하는 방식**입니다. 단일 모듈(`:app` 하나)에 모든 코드를 넣는 대신, 기능과 책임에 따라 `:feature:login`, `:core:network`, `:core:data` 같은 독립 모듈로 분리합니다.

각 모듈은 자신의 `build.gradle(.kts)`를 가지며, **어떤 모듈에 의존할지를 명시적으로 선언**합니다. 즉 모듈 간 의존 관계가 빌드 스크립트에 코드로 드러납니다.

```kotlin
// feature/login/build.gradle.kts
dependencies {
    implementation(project(":core:data"))
    implementation(project(":core:designsystem"))
    // :feature:home 에는 의존하지 않는다 → 컴파일 단계에서 강제됨
}
```

분리 자체가 목적이 아니라, 이 분리를 통해 **캡슐화·빌드 속도·의존 관계의 명시성**이라는 실질적 이득을 얻는 것이 핵심입니다.

## feature와 core 모듈의 분리 {#feature-core-split}

멀티모듈을 처음 도입할 때 가장 흔하고 검증된 분류 기준은 **feature 모듈**과 **core 모듈**입니다.

### core 모듈: 공통 기반 {#core-module}

`core` 모듈은 여러 화면이 공통으로 쓰는 **재사용 가능한 기반 코드**를 담습니다. 특정 화면에 종속되지 않으며, 그 자체로 완결된 책임 단위입니다.

- `:core:network` — Retrofit/OkHttp 설정, 인터셉터 등 네트워크 클라이언트
- `:core:database` — Room 데이터베이스, DAO
- `:core:data` — Repository 구현, 네트워크와 DB를 합쳐 도메인 데이터를 제공
- `:core:designsystem` — 공통 Compose 컴포넌트, 테마, 색상
- `:core:common` — 디스패처, 결과 래퍼 등 순수 유틸

### feature 모듈: 화면 단위 {#feature-module}

`feature` 모듈은 **사용자에게 보이는 하나의 화면(또는 밀접한 화면 묶음)** 을 담습니다. ViewModel, Composable UI, 그 화면 전용 상태가 들어갑니다.

- `:feature:login`, `:feature:home`, `:feature:settings`

### 왜 이렇게 나누는가 {#why-feature-core}

핵심은 **feature끼리는 서로 모르고, core를 공유한다**는 점입니다. `:feature:home`을 수정해도 `:feature:settings`는 영향받지 않으므로, 변경의 파급 범위가 모듈 경계 안으로 제한됩니다. 또한 새 화면을 추가할 때 기존 core를 조립하기만 하면 되므로 기능 확장이 예측 가능해집니다.

`:app` 모듈은 보통 가장 얇으며, 모든 feature를 모아 내비게이션으로 연결하고 의존성 그래프의 진입점(Application 클래스 등) 역할만 합니다.

## 의존 방향: 단방향과 순환 금지 {#dependency-direction}

모듈을 나누는 것보다 **의존이 어느 방향으로 흐르는가**를 통제하는 것이 멀티모듈 설계의 본질입니다.

### 단방향 규칙 {#one-way-rule}

올바른 의존 방향은 다음 한 방향으로 고정됩니다.

```
app  →  feature  →  core
```

- `:app`은 `:feature`들에 의존합니다.
- `:feature`는 `:core`들에 의존합니다.
- **`:core`는 절대 `:feature`나 `:app`에 의존하지 않습니다.**
- **`:feature`는 다른 `:feature`에 의존하지 않습니다.**

저수준(core)이 고수준(feature)을 모르게 하는 것은 의존성 역전 원칙(DIP)과도 맞닿아 있습니다. core가 feature를 알게 되는 순간 재사용성과 독립 빌드가 모두 깨집니다.

### 순환 의존은 빌드 자체가 실패한다 {#no-cycles}

Gradle은 모듈 의존 그래프가 **비순환(DAG)** 이어야 합니다. `:core:data`가 `:feature:home`에 의존하고 그 `:feature:home`이 다시 `:core:data`에 의존하면, Gradle은 대표적으로 `Circular dependency between the following tasks` 오류로 빌드를 거부합니다.

두 feature가 공통 코드를 필요로 한다면 그 코드를 **아래쪽 core 모듈로 내려야** 합니다. feature 간 직접 의존으로 해결하면 안 됩니다.

```text
잘못됨:  :feature:home → :feature:profile   (feature 간 직접 의존)
올바름:  :feature:home → :core:user ← :feature:profile  (공통은 core로)
```

이렇게 단방향·비순환을 강제하면 의존 그래프가 트리에 가까워지고, 모듈을 병렬로 컴파일할 여지가 커집니다.

## api vs implementation {#api-vs-implementation}

Gradle은 의존성을 선언할 때 그 의존성이 **모듈 외부로 노출되는지**를 키워드로 구분합니다. 이것이 멀티모듈에서 캡슐화와 빌드 속도를 동시에 좌우합니다.

### 두 키워드의 의미 차이 {#api-impl-meaning}

`A → B → C` 구조(`:app`이 `:feature`에, `:feature`가 `:core`에 의존)를 가정합니다.

- **`implementation`**: B가 C를 `implementation`으로 선언하면, **C는 B의 내부 구현 세부사항**이 됩니다. B를 쓰는 A는 C를 컴파일 클래스패스에서 볼 수 없습니다. C의 타입은 B의 공개 API 시그니처에 등장하지 않습니다.
- **`api`**: B가 C를 `api`로 선언하면, **C가 B의 공개 API의 일부로 전이(transitive) 노출**됩니다. A는 C의 타입을 직접 쓸 수 있습니다.

```kotlin
// :core:data 의 build.gradle.kts
dependencies {
    // model 타입이 Repository 시그니처에 등장 → 소비자도 알아야 함
    api(project(":core:model"))

    // Room은 내부에서만 쓰고 외부엔 숨김
    implementation(libs.androidx.room.runtime)
}
```

위에서 `:feature:home`이 `:core:data`를 쓰면 `:core:model`의 타입은 보이지만, Room 관련 타입은 보이지 않습니다. 구현 라이브러리가 자연스럽게 캡슐화됩니다.

### 빌드 속도에 미치는 영향 {#api-impl-build}

차이의 실질적 효과는 **재컴파일 범위**입니다.

- `implementation`으로 선언된 C의 **내부 구현**이 바뀌어도(공개 ABI는 그대로), C가 다시 컴파일되고 B는 다시 컴파일될 수 있으며 **A는 재컴파일되지 않습니다.** C가 A의 컴파일 클래스패스에 없기 때문입니다.
- `api`로 선언하면 C가 A의 컴파일 클래스패스에 있으므로, C의 ABI 변경이 A까지 재컴파일을 유발할 수 있습니다.

그래서 **기본은 `implementation`을 쓰고, 타입이 정말로 공개 API 시그니처에 새어 나가야 할 때만 `api`** 를 씁니다. `api`를 남발하면 한 모듈의 작은 변경이 그래프 위쪽 전체의 재컴파일을 부르고, 멀티모듈로 얻으려던 빌드 이득이 사라집니다.

## 빌드 속도와 캡슐화 {#build-speed-encapsulation}

멀티모듈을 채택하는 두 가지 핵심 동기가 빌드 속도와 캡슐화입니다.

### 빌드 속도: 병렬·증분·캐시 {#build-speed}

단일 모듈에서는 파일 하나만 고쳐도 모듈 전체가 재컴파일 대상이 되기 쉽습니다. 멀티모듈은 이를 세 가지 메커니즘으로 줄입니다.

1. **병렬 빌드**: 서로 의존하지 않는 모듈은 Gradle이 동시에 컴파일합니다(`org.gradle.parallel=true`). 의존 그래프가 넓고 얕을수록 병렬화 여지가 큽니다.
2. **증분 빌드**: 바뀐 모듈과 그 모듈에 (컴파일 클래스패스로) 의존하는 모듈만 다시 빌드됩니다. `:feature:login` 한 줄을 고쳐도 `:feature:home`은 빌드되지 않습니다.
3. **빌드 캐시**: 입력이 동일한 모듈의 컴파일 결과는 캐시에서 재사용됩니다(`org.gradle.caching=true`). 변경 없는 core 모듈은 매번 다시 빌드하지 않습니다.

앞서 본 `implementation`/`api` 구분이 여기서 직접 작동합니다. `implementation` 위주로 구성된 그래프일수록 변경의 재컴파일 전파가 짧아집니다.

### 캡슐화: 잘못된 접근을 컴파일 단계에서 막는다 {#encapsulation}

단일 모듈에서 `internal`은 **모듈 경계 안에서만** 동작합니다. 같은 모듈이면 어디서든 접근할 수 있으므로, 코드가 커지면 의도치 않은 결합이 생깁니다.

멀티모듈에서는 모듈 경계 자체가 캡슐화 단위가 됩니다.

- 모듈에 의존성을 선언하지 않으면 그 모듈의 `public` 타입조차 **컴파일 시점에 보이지 않습니다.**
- `internal`로 선언한 타입은 그 모듈 밖에서 절대 접근할 수 없습니다.

그 결과 "이 클래스는 이 모듈 안에서만 쓰여야 한다"는 설계 의도가 **문서나 관습이 아니라 컴파일러로 강제**됩니다. 잘못된 의존을 추가하려면 `build.gradle`을 명시적으로 고쳐야 하므로, 리뷰에서 아키텍처 위반이 눈에 띕니다.

### 비용도 있다 {#tradeoffs}

멀티모듈은 공짜가 아닙니다. 모듈 수가 늘면 빌드 스크립트 보일러플레이트, 모듈 경계 설계 부담, 초기 클린 빌드 시간(모듈 설정 오버헤드)이 늘어납니다. 그래서 작은 앱에서는 과합니다. **빌드 시간이 길어지고, 화면/팀이 늘어 변경 충돌이 잦아질 때** 도입 효과가 분명해집니다. 공통 설정은 convention plugin(여러 모듈이 반복하는 Gradle 설정을 하나의 커스텀 플러그인으로 묶어 각 모듈에서 적용만 하는 방식)으로 묶어 보일러플레이트를 줄이는 것이 보통입니다.

## 요약 {#summary}

> **TL;DR** — 멀티모듈은 앱을 `:feature`(화면)와 `:core`(공통 기반)로 쪼개 `app → feature → core` 단방향·비순환 의존으로 묶는 구조입니다. 의존 선언 시 기본은 `implementation`(구현 은닉, 재컴파일 범위 최소화), 타입이 공개 시그니처에 노출될 때만 `api`를 씁니다. 이를 통해 병렬·증분·캐시 빌드로 빌드 속도를 얻고, 모듈 경계로 캡슐화를 컴파일 단계에서 강제합니다.

1. **feature·core 분리**: feature는 화면 단위, core는 공통 기반. feature끼리는 서로 모르고 core를 공유한다.
2. **의존 방향**: `app → feature → core` 단방향만 허용하고 순환을 금지한다. core는 feature를 몰라야 하며, feature 공통 코드는 아래 core로 내린다.
3. **api vs implementation**: `implementation`은 의존성을 숨기고 재컴파일 전파를 막는 기본값, `api`는 타입을 전이 노출해야 할 때만 쓴다.
4. **빌드 속도·캡슐화**: 병렬·증분·캐시 빌드로 속도를, 모듈 경계와 `internal`로 컴파일 시점 캡슐화를 얻는다. 대신 모듈 관리 비용이 따른다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 멀티모듈에서 feature 모듈과 core 모듈은 각각 무엇을 담고, 왜 그렇게 나누나요?">

feature 모듈은 사용자에게 보이는 하나의 화면 또는 밀접한 화면 묶음을 담습니다. ViewModel, Composable UI, 그 화면 전용 상태가 들어갑니다(`:feature:login`, `:feature:home` 등). core 모듈은 여러 화면이 공통으로 쓰는 재사용 가능한 기반 코드를 담습니다. 네트워크, 데이터베이스, Repository, 디자인 시스템 등 특정 화면에 종속되지 않는 코드입니다(`:core:network`, `:core:data` 등).

이렇게 나누는 이유는 feature끼리는 서로 모르고 core만 공유하게 하기 위함입니다. 그러면 한 화면을 수정해도 다른 화면이 영향받지 않아 변경의 파급 범위가 모듈 경계 안으로 제한되고, 새 화면은 기존 core를 조립해 추가하므로 확장이 예측 가능해집니다.

</def>
<def title="Q) 모듈 간 의존 방향은 어떻게 통제해야 하나요? 순환 의존이 생기면 어떻게 되나요?">

의존은 `app → feature → core` 한 방향으로 고정합니다. app은 feature에, feature는 core에 의존하며, core는 절대 feature나 app에 의존하지 않고 feature끼리도 직접 의존하지 않습니다. 저수준(core)이 고수준(feature)을 모르게 해야 재사용성과 독립 빌드가 유지됩니다.

Gradle의 모듈 그래프는 비순환(DAG)이어야 하므로, 두 모듈이 서로 의존하는 순환이 생기면 `Circular dependency` 오류로 빌드 자체가 실패합니다. 두 feature가 공통 코드를 필요로 한다면 feature 간 직접 의존이 아니라 그 코드를 아래쪽 core 모듈로 내려서 둘 다 그 core에 의존하게 풀어야 합니다.

</def>
<def title="Q) implementation과 api의 차이는 무엇이며, 멀티모듈에서 어느 것을 기본으로 써야 하나요?">

`A → B → C` 구조에서 B가 C를 `implementation`으로 선언하면 C는 B의 내부 구현 세부사항이 되어, B를 쓰는 A의 컴파일 클래스패스에는 C가 보이지 않습니다. `api`로 선언하면 C가 B의 공개 API로 전이 노출되어 A도 C의 타입을 직접 쓸 수 있습니다.

기본값은 `implementation`이고, 타입이 정말로 그 모듈의 공개 API 시그니처에 등장해 소비자도 알아야 할 때만 `api`를 씁니다. 이유는 두 가지입니다. 첫째, `implementation`은 구현 라이브러리를 캡슐화해 소비자가 의도치 않게 의존하는 것을 막습니다. 둘째, `implementation`으로 선언된 의존성의 내부 구현이 바뀌어도 A는 재컴파일되지 않아 재컴파일 전파 범위가 짧아집니다. `api`를 남발하면 작은 변경이 그래프 위쪽 전체의 재컴파일을 유발해 빌드 이득이 사라집니다.

</def>
<def title="Q) 멀티모듈이 빌드 속도를 어떻게 개선하나요?">

세 가지 메커니즘으로 개선합니다. 첫째, 병렬 빌드입니다. 서로 의존하지 않는 모듈은 Gradle이 동시에 컴파일하므로(`org.gradle.parallel`), 의존 그래프가 넓고 얕을수록 병렬화 여지가 큽니다. 둘째, 증분 빌드입니다. 바뀐 모듈과 그 모듈에 컴파일 클래스패스로 의존하는 모듈만 다시 빌드되므로, 한 feature를 고쳐도 무관한 feature는 빌드되지 않습니다. 셋째, 빌드 캐시입니다. 입력이 동일한 모듈의 컴파일 결과는 캐시에서 재사용되어(`org.gradle.caching`) 변경 없는 core는 다시 빌드하지 않습니다.

이때 `implementation` 위주로 의존을 선언할수록 변경의 재컴파일 전파가 짧아져 증분 빌드 효과가 커집니다.

</def>
<def title="Q) 멀티모듈은 캡슐화를 어떻게 강화하나요? 단일 모듈의 internal과 무엇이 다른가요?">

단일 모듈에서 `internal`은 모듈 경계 안에서만 동작하므로, 같은 모듈이면 어디서든 접근할 수 있어 코드가 커지면 의도치 않은 결합이 생깁니다. 멀티모듈에서는 모듈 경계 자체가 캡슐화 단위가 됩니다. 어떤 모듈에 의존성을 선언하지 않으면 그 모듈의 public 타입조차 컴파일 시점에 보이지 않고, internal 타입은 그 모듈 밖에서 절대 접근할 수 없습니다.

그 결과 "이 코드는 이 모듈 안에서만 쓰여야 한다"는 설계 의도가 관습이 아니라 컴파일러로 강제됩니다. 잘못된 의존을 추가하려면 `build.gradle`을 명시적으로 고쳐야 하므로 아키텍처 위반이 코드 리뷰에서 드러납니다. 다만 모듈 수가 늘면 빌드 스크립트 보일러플레이트와 모듈 설계 부담이라는 비용이 따르므로, 빌드 시간이 길어지고 팀/화면이 많아질 때 도입 효과가 분명합니다.

</def>
</deflist>
