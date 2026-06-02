# Q67) Gradle 의존성 관리

## 의존성 선언의 기초 {#C0}

안드로이드 모듈은 외부 라이브러리나 다른 모듈에 의존합니다. 이 의존성은 모듈의 `build.gradle.kts`에 **설정(configuration)** 과 **좌표(coordinate)** 로 선언합니다.

```kotlin
dependencies {
    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    //  ^설정         ^group         ^name     ^version
}
```

- **좌표**: `group:name:version` 형식으로 어떤 아티팩트인지 식별합니다.
- **설정**: 그 의존성을 **언제(컴파일/런타임)**, 그리고 **누구에게(자기 모듈만/소비자에게도)** 노출할지 결정합니다.

이 토픽의 핵심은 세 가지입니다. 첫째, 버전과 좌표를 어디에 어떻게 모아 관리하는가(**버전 카탈로그**). 둘째, 설정 중 가장 자주 쓰는 `api`와 `implementation`이 무엇이 다른가. 셋째, 이 의존성들이 모여 만드는 **의존성 그래프**가 빌드 시 어떻게 해석되는가입니다.

## 버전 카탈로그 {#version-catalog}

### 정의와 동기 {#catalog-motivation}

버전 카탈로그(version catalog)는 **의존성 좌표와 버전을 한 곳에 모아 type-safe하게 참조하는 Gradle 표준 기능**입니다. 기본 위치는 `gradle/libs.versions.toml`입니다. Gradle **7.0에서 도입(incubating)** 되었고, 이때는 `settings.gradle(.kts)`에 `enableFeaturePreview("VERSION_CATALOGS")`를 명시해야 쓸 수 있는 미리보기 기능이었습니다. **Gradle 7.4에서 안정화(stable)** 되면서 그 플래그 없이 바로 사용할 수 있게 되었습니다.

동기는 명확합니다. 카탈로그가 없으면 같은 라이브러리 버전 문자열이 여러 모듈의 `build.gradle.kts`에 흩어집니다. 멀티 모듈 프로젝트에서 Retrofit 버전을 올리려면 모든 모듈을 일일이 찾아 고쳐야 하고, 한 모듈만 빠뜨리면 버전이 어긋납니다. 카탈로그는 이 좌표·버전을 **단일 출처(single source of truth)** 로 만듭니다.

### TOML 구조 {#toml-structure}

`libs.versions.toml`은 네 개의 테이블로 구성됩니다.

```toml
[versions]
retrofit = "2.11.0"
okhttp = "4.12.0"

[libraries]
retrofit = { group = "com.squareup.retrofit2", name = "retrofit", version.ref = "retrofit" }
okhttp = { module = "com.squareup.okhttp3:okhttp", version.ref = "okhttp" }

[bundles]
network = ["retrofit", "okhttp"]

[plugins]
android-application = { id = "com.android.application", version = "8.5.0" }
```

- **`[versions]`**: 버전 숫자만 모읍니다. `version.ref`로 여러 라이브러리가 공유합니다.
- **`[libraries]`**: 라이브러리 좌표를 정의합니다. `module = "group:name"` 또는 `group`/`name`을 따로 적습니다.
- **`[bundles]`**: 함께 쓰는 라이브러리를 묶어 한 줄로 추가하게 합니다.
- **`[plugins]`**: Gradle 플러그인을 정의해 `plugins {}` 블록에서 참조합니다.

### 참조 방식 {#catalog-reference}

카탈로그를 정의하면 Gradle이 `libs`라는 **type-safe accessor**를 자동 생성합니다. TOML의 점·하이픈은 accessor에서 점으로 변환됩니다(`androidx-core-ktx` → `libs.androidx.core.ktx`).

```kotlin
dependencies {
    implementation(libs.retrofit)        // [libraries]의 retrofit
    implementation(libs.bundles.network) // [bundles]의 network 전체
}
```

`libs`는 IDE 자동완성과 오타 검출을 지원합니다. 존재하지 않는 라이브러리를 참조하면 빌드 스크립트 컴파일 단계에서 바로 실패하므로, 문자열로 직접 좌표를 적을 때보다 오류를 일찍 잡습니다.

## api vs implementation {#api-vs-implementation}

### 두 설정의 차이 {#config-difference}

`api`와 `implementation`은 둘 다 의존성을 **컴파일·런타임 양쪽에서** 사용 가능하게 만듭니다. 차이는 단 하나, **그 의존성을 이 모듈을 사용하는 소비자(consumer)에게 전이(transitive)시켜 노출하는가**입니다.

- **`implementation`**: 의존성을 **자기 모듈 내부에서만** 사용합니다. 이 모듈을 의존하는 다른 모듈의 컴파일 클래스패스에는 노출되지 않습니다.
- **`api`**: 의존성을 **소비자의 컴파일 클래스패스로 전이**시킵니다. 소비자는 이 모듈을 통해 해당 라이브러리 타입을 직접 사용할 수 있습니다.

### 동작 예시 {#config-example}

`:network` 모듈이 Retrofit에 의존하고, `:app` 모듈이 `:network`에 의존하는 상황을 봅니다.

```kotlin
// :network 모듈의 build.gradle.kts
dependencies {
    api(libs.retrofit)              // 또는 implementation(libs.retrofit)
}
```

```kotlin
// :app 모듈
dependencies {
    implementation(project(":network"))
}
```

`:network`가 `api(libs.retrofit)`로 선언하면, `:app`은 `Retrofit` 타입을 import해 직접 쓸 수 있습니다. 반면 `implementation(libs.retrofit)`로 선언하면, `:app`의 컴파일 클래스패스에서 `Retrofit` 타입이 보이지 않아 import가 컴파일 에러가 됩니다. 다만 `:network`가 내부적으로 Retrofit을 쓰는 동작 자체는 런타임에 정상이며, `:app`은 `:network`가 제공하는 자체 API만 사용하게 됩니다. 여기서 `api`와 `implementation`의 차이는 **컴파일 클래스패스 전이 여부**일 뿐이라는 점을 분명히 해 둡니다. 두 설정 모두 해당 의존성을 소비자의 **런타임 클래스패스**에는 전이시키므로, `implementation`으로 선언해도 런타임에 Retrofit 클래스는 정상적으로 로드됩니다.

### 왜 implementation을 기본으로 쓰는가 {#why-implementation-default}

권장 기본값은 `implementation`이며, 이유는 두 가지입니다.

1. **컴파일 격리로 빌드 속도 향상**: `implementation`으로 선언한 의존성의 **구현부(ABI에 영향 없는 내부 변경)** 가 바뀌어도 소비자 모듈은 재컴파일되지 않습니다. `api`는 소비자 클래스패스에 노출되므로, 그 의존성 변경이 소비자 재컴파일을 유발해 멀티 모듈에서 빌드 비용이 커집니다.
2. **캡슐화**: 내부 구현 라이브러리가 소비자에게 새어 나가지 않습니다. `:network`가 내부에서 OkHttp를 쓴다는 사실을 `:app`이 알 필요가 없다면 `implementation`으로 숨기는 것이 맞습니다.

`api`는 그 의존성의 타입이 **이 모듈의 공개 API 시그니처에 등장할 때만** 사용합니다. 예를 들어 `:network`의 public 함수가 `Retrofit` 객체를 반환한다면, 소비자가 그 반환 타입을 다뤄야 하므로 `api`가 필요합니다.

## 의존성 그래프와 해석 {#dependency-graph}

### 전이 의존성과 그래프 {#transitive-graph}

모듈이 선언한 의존성은 다시 자신의 의존성을 가지므로, 전체 의존성은 **방향 그래프(directed graph)** 를 이룹니다. 내가 Retrofit 하나만 선언해도, Retrofit이 OkHttp에, OkHttp가 Okio에 의존하는 식으로 **전이 의존성(transitive dependency)** 이 그래프를 따라 끌려 들어옵니다.

```text
:app
 └─ :network
     └─ retrofit:2.11.0
         └─ okhttp:4.12.0
             └─ okio:3.6.0
```

이 그래프에서 `api`/`implementation`은 **각 간선이 다음 단계로 전파되는지**를 결정하고, 버전 카탈로그는 **각 노드의 버전 좌표**를 공급합니다. 세 핵심 개념이 여기서 만납니다.

### 버전 충돌과 해석 전략 {#version-conflict}

같은 라이브러리가 서로 다른 버전으로 그래프에 두 번 이상 등장할 수 있습니다. 라이브러리 A는 Okio 3.2를, 라이브러리 B는 Okio 3.5를 요구하는 식입니다. JVM 런타임에는 한 클래스패스에 한 버전만 존재할 수 있으므로 Gradle이 하나를 골라야 합니다.

Gradle의 기본 전략은 **highest version wins(가장 높은 버전 선택)** 입니다. 위 예시에서는 Okio 3.5가 선택되고 3.2 요구는 3.5로 업그레이드됩니다. 이는 Maven의 "가까운 의존성 우선(nearest-wins)"과 다른 점으로, 면접에서 자주 확인하는 부분입니다. 단, 이것은 어디까지나 기본 동작이며, 뒤에서 다룰 `resolutionStrategy.force`나 strict version 제약을 걸면 선택을 강제할 수 있어, 더 높은 버전이 그래프에 있어도 더 낮은 버전으로 다운그레이드시킬 수 있습니다.

### 해석 강제와 확인 {#resolution-control}

자동 선택이 원하는 결과가 아닐 때를 위해 Gradle은 제어 수단을 제공합니다.

```kotlin
configurations.all {
    resolutionStrategy {
        force("com.squareup.okio:okio:3.9.0")   // 특정 버전으로 고정
    }
}
```

그래프 해석 결과를 확인하려면 `dependencies` 태스크를 씁니다. 어떤 버전이 최종 선택됐고 무엇이 업그레이드(`->`)됐는지 보여 줍니다.

```bash
./gradlew :app:dependencies --configuration releaseRuntimeClasspath
```

정리하면, 의존성 그래프는 선언한 좌표에서 시작해 전이 의존성으로 확장되고, 충돌은 highest-wins로 해석되며, 최종적으로 **각 설정(configuration)별로 하나의 일관된 클래스패스**로 평탄화(flatten)됩니다.

## 요약 {#summary}

> **TL;DR** — 의존성은 `group:name:version` 좌표를 설정에 담아 선언합니다. 버전 카탈로그(`libs.versions.toml`)는 좌표·버전을 단일 출처로 모아 type-safe하게 참조하게 합니다(Gradle 7.0 도입, 7.4 안정화). `api`는 의존성을 소비자에게 전이·노출하고 `implementation`은 자기 모듈에 가둬 빌드 격리와 캡슐화를 얻으므로 기본은 `implementation`입니다. 선언한 의존성은 전이 의존성과 함께 방향 그래프를 이루고, 버전 충돌은 Gradle의 highest-version-wins로 해석되어 설정별 단일 클래스패스로 평탄화됩니다.

1. **버전 카탈로그**: `gradle/libs.versions.toml`에 좌표·버전을 모아 단일 출처로 만들고, 자동 생성된 `libs` accessor로 type-safe하게 참조한다. Gradle 7.0에서 도입돼 7.4에서 안정화됐다.
2. **api vs implementation**: 차이는 소비자에게 전이 노출하는가뿐이다. `api`는 노출, `implementation`은 모듈 내부에 격리. 빌드 속도와 캡슐화 때문에 기본은 `implementation`이며, `api`는 그 타입이 공개 API 시그니처에 등장할 때만 쓴다.
3. **의존성 그래프**: 선언한 의존성과 전이 의존성이 방향 그래프를 이루고, 버전 충돌은 highest-version-wins로 해석되어 설정별 단일 클래스패스로 평탄화된다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 버전 카탈로그(version catalog)란 무엇이고 왜 쓰나요?">

버전 카탈로그는 의존성 좌표와 버전을 한 곳에 모아 type-safe하게 참조하는 Gradle 표준 기능입니다. 기본 위치는 `gradle/libs.versions.toml`이고 `[versions]`, `[libraries]`, `[bundles]`, `[plugins]` 테이블로 구성됩니다. Gradle 7.0에서 미리보기로 도입되어 7.4에서 안정화됐으므로, 7.4 이상에서는 별도 플래그 없이 바로 쓸 수 있습니다.

쓰는 이유는 버전과 좌표를 단일 출처로 만들기 위해서입니다. 카탈로그가 없으면 같은 라이브러리 버전 문자열이 여러 모듈에 흩어져, 버전을 올릴 때 모든 모듈을 고쳐야 하고 한 곳만 빠뜨리면 버전이 어긋납니다. 카탈로그를 정의하면 Gradle이 `libs` accessor를 자동 생성해 `libs.retrofit`처럼 참조하게 하며, 오타나 존재하지 않는 라이브러리는 빌드 스크립트 컴파일 단계에서 바로 잡힙니다.

</def>
<def title="Q) api와 implementation의 차이는 무엇인가요? 기본으로 무엇을 권장하나요?">

둘 다 의존성을 컴파일·런타임 양쪽에서 쓸 수 있게 하지만, 차이는 그 의존성을 이 모듈의 소비자에게 전이(transitive)시켜 노출하는가입니다. `api`는 의존성을 소비자의 컴파일 클래스패스로 전이시켜 소비자가 그 타입을 직접 쓸 수 있게 하고, `implementation`은 자기 모듈 내부에만 가둬 소비자에게 노출하지 않습니다.

기본 권장은 `implementation`입니다. 첫째, 구현부가 바뀌어도 소비자 모듈이 재컴파일되지 않아 멀티 모듈 빌드가 빨라집니다(컴파일 격리). 둘째, 내부 구현 라이브러리가 소비자에게 새어 나가지 않습니다(캡슐화). `api`는 그 의존성의 타입이 이 모듈의 공개 API 시그니처(반환 타입·파라미터 등)에 등장해 소비자가 반드시 그 타입을 다뤄야 할 때만 씁니다.

</def>
<def title="Q) api로 선언해야만 하는 경우는 언제인가요?">

이 모듈의 public API 시그니처에 그 의존성의 타입이 직접 등장할 때입니다. 예를 들어 `:network` 모듈의 public 함수가 `Retrofit` 객체를 반환하거나 파라미터로 받는다면, 소비자인 `:app`이 그 타입을 컴파일 시점에 알아야 하므로 `:network`는 Retrofit을 `api`로 선언해야 합니다.

반대로 `:network`가 Retrofit을 내부 구현 세부로만 쓰고 외부에는 자체적인 API만 노출한다면 `implementation`이 맞습니다. `api`로 선언하면 그 의존성의 변경이 소비자 재컴파일을 유발하고 캡슐화도 깨지므로, 시그니처 노출이 없는데 `api`를 쓰는 것은 불필요한 비용입니다.

</def>
<def title="Q) 의존성 그래프에서 같은 라이브러리의 버전이 충돌하면 Gradle은 어떻게 해석하나요?">

선언한 의존성은 전이 의존성과 함께 방향 그래프를 이루는데, 같은 라이브러리가 서로 다른 버전으로 그래프에 두 번 이상 등장할 수 있습니다. JVM 런타임 클래스패스에는 한 버전만 존재할 수 있으므로 Gradle이 하나를 골라야 합니다.

Gradle의 기본 전략은 highest version wins, 즉 충돌하는 버전 중 가장 높은 버전을 선택하고 나머지 요구를 그 버전으로 업그레이드하는 것입니다. 이는 Maven의 nearest-wins(가장 가까운 의존성 우선)와 다릅니다. 원하는 버전을 강제하려면 `resolutionStrategy.force(...)`를 쓰고, 최종 선택 결과는 `./gradlew :app:dependencies` 태스크로 어떤 버전이 선택되고 무엇이 업그레이드(`->`)됐는지 확인할 수 있습니다.

</def>
<def title="Q) implementation으로 선언한 의존성이 빌드 속도에 어떻게 도움이 되나요?">

`implementation`은 의존성을 소비자의 컴파일 클래스패스에 노출하지 않으므로, 그 의존성의 ABI에 영향을 주지 않는 내부 구현 변경이 일어나도 소비자 모듈을 재컴파일할 필요가 없습니다. 멀티 모듈 프로젝트에서 이 컴파일 격리는 변경 전파 범위를 줄여 증분 빌드를 빠르게 합니다.

반면 `api`로 선언한 의존성은 소비자 클래스패스에 그대로 노출되므로, 그 의존성이 바뀌면 그것을 보는 모든 소비자 모듈이 재컴파일 대상이 됩니다. 따라서 모듈 경계에서 노출이 꼭 필요하지 않은 의존성을 `implementation`으로 두는 것이 빌드 비용을 줄이는 기본 원칙입니다.

</def>
</deflist>
