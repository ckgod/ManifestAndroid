# Q69) Build Variants와 BuildConfig

안드로이드 앱은 하나의 소스 코드로 디버그용·릴리스용, 또는 무료판·유료판처럼 서로 다른 결과물을 만들어야 할 때가 많습니다. Gradle은 이를 **Build Variant(빌드 변형)** 개념으로 다루고, 빌드별로 달라지는 값은 **BuildConfig**라는 생성 클래스로 코드에 주입합니다. 이 토픽은 그 두 메커니즘과, 코드에서 빌드별로 분기하는 방법을 다룹니다.

## buildType과 product flavor {#build-type-and-flavor}

Build Variant는 두 축의 조합으로 결정됩니다. 하나는 **buildType**, 다른 하나는 **product flavor**입니다.

### buildType {#build-type}

`buildType`은 **같은 앱을 어떤 방식으로 빌드할지**를 정의합니다. 코드의 기능 자체보다는 컴파일·패키징 설정에 관여합니다. 기본으로 `debug`와 `release` 두 개가 제공됩니다.

- `debug`: 개발용. 자동으로 디버그 서명, `debuggable true`가 적용됩니다.
- `release`: 배포용. 보통 코드 축소(`minifyEnabled`)와 릴리스 서명을 붙입니다.

```kotlin
// app/build.gradle.kts
android {
    buildTypes {
        getByName("debug") {
            applicationIdSuffix = ".debug"   // 같은 기기에 release와 동시 설치 가능
            isDebuggable = true
        }
        getByName("release") {
            isMinifyEnabled = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
}
```

### product flavor {#product-flavor}

`productFlavor`는 **같은 코드 베이스에서 만들어 내는 서로 다른 버전의 앱**을 정의합니다. 무료/유료, 회사 A용/회사 B용처럼 기능·리소스·식별자가 갈리는 변종을 표현합니다. flavor는 `flavorDimensions`(차원)에 속하며, 차원이 여러 개면 각 차원에서 하나씩 골라 조합됩니다.

```kotlin
android {
    flavorDimensions += "tier"
    productFlavors {
        create("free") {
            dimension = "tier"
            applicationIdSuffix = ".free"
            versionNameSuffix = "-free"
        }
        create("paid") {
            dimension = "tier"
            applicationIdSuffix = ".paid"
        }
    }
}
```

### Variant는 둘의 곱 {#variant-is-product}

최종 Build Variant는 `flavor × buildType`의 조합입니다. 위처럼 flavor 2개(`free`, `paid`)와 buildType 2개(`debug`, `release`)가 있으면 변형은 `freeDebug`, `freeRelease`, `paidDebug`, `paidRelease` 4개가 됩니다. flavor를 하나도 선언하지 않으면 buildType만으로 `debug`, `release` 2개의 variant가 생깁니다.

> **buildType과 flavor의 책임 구분**: buildType은 "어떻게 빌드/패키징하는가"(서명·축소·디버그 여부), flavor는 "어떤 제품인가"(기능·식별자·리소스)를 담당합니다. 둘 다 `applicationIdSuffix`를 가질 수 있어, 한 기기에 여러 variant를 동시에 설치할 수 있습니다.

## BuildConfig 주입 {#buildconfig-injection}

### BuildConfig란 {#what-is-buildconfig}

`BuildConfig`는 **Gradle이 빌드 시 자동 생성하는 final 클래스**입니다. 빌드 설정에 정의한 값들이 컴파일 타임 상수로 들어가, 코드에서 정적으로 읽을 수 있습니다. 기본 제공 필드는 다음과 같습니다.

- `BuildConfig.DEBUG`: 디버그 빌드 여부(`Boolean`).
- `BuildConfig.APPLICATION_ID`: 최종 applicationId.
- `BuildConfig.BUILD_TYPE`: buildType 이름 문자열.
- `BuildConfig.FLAVOR`: 선택된 flavor 이름(flavor가 있을 때).
- `BuildConfig.VERSION_CODE`, `BuildConfig.VERSION_NAME`.

### 커스텀 필드 추가 {#custom-buildconfig-fields}

`buildConfigField`로 빌드별 값을 직접 주입할 수 있습니다. API 엔드포인트, 키, 기능 플래그처럼 variant마다 달라지는 값을 코드 수정 없이 빌드 설정에서 제어할 때 씁니다.

```kotlin
android {
    // AGP 8.0+ 에서는 buildConfig 생성을 명시적으로 켜야 한다
    buildFeatures {
        buildConfig = true
    }

    buildTypes {
        getByName("debug") {
            buildConfigField("String", "BASE_URL", "\"https://dev.api.example.com\"")
        }
        getByName("release") {
            buildConfigField("String", "BASE_URL", "\"https://api.example.com\"")
        }
    }
}
```

위 설정에서 생성되는 코드는 다음과 같습니다. 세 번째 인자는 **자바 소스에 그대로 박히는 리터럴**이므로, 문자열은 따옴표(`\"...\"`)까지 직접 넣어야 합니다.

```kotlin
// 자동 생성된 BuildConfig (debug variant)
public final class BuildConfig {
    public static final String BASE_URL = "https://dev.api.example.com";
}
```

```kotlin
// 코드에서 사용
val client = Retrofit.Builder()
    .baseUrl(BuildConfig.BASE_URL)   // variant에 따라 자동으로 결정됨
    .build()
```

### 왜 BuildConfig인가 {#why-buildconfig}

이 값들은 컴파일 타임 상수이므로 **런타임 조건 분기 없이 정적으로 확정**됩니다. R8/ProGuard는 release 빌드에서 `if (BuildConfig.DEBUG)`처럼 항상 false로 평가되는 가지를 **데드 코드로 제거**합니다. 즉 디버그 전용 로직이 릴리스 바이너리에 아예 포함되지 않아, 코드 노출과 용량 측면에서 유리합니다.

주의할 점은 `buildConfigField`로 넣은 값이 **APK 안에 평문으로 남는다**는 것입니다. 따라서 API base URL 같은 비밀이 아닌 구성에는 적합하지만, 실제 비밀 키를 여기에 그대로 넣으면 디컴파일로 노출됩니다. 비밀은 서버 측 보관이나 별도 보안 저장소를 써야 합니다.

> `resValue`는 BuildConfig 필드 대신 **리소스(R.string 등)**를 variant별로 생성합니다. 코드에서 상수로 읽을 값은 `buildConfigField`, XML이나 리소스로 참조할 값(앱 이름 등)은 `resValue`를 씁니다.

## 빌드별 분기 {#build-time-branching}

variant마다 동작을 다르게 하는 방법은 크게 두 갈래입니다. **런타임 분기**와 **소스 세트(source set) 분기**입니다.

### 런타임 분기 {#runtime-branching}

BuildConfig 값을 `if`로 검사해 동작을 가르는 방식입니다. 코드가 한 곳에 있어 추적이 쉽고, release에서는 R8이 죽은 가지를 제거합니다.

```kotlin
fun setupLogging() {
    if (BuildConfig.DEBUG) {
        Timber.plant(Timber.DebugTree())   // debug에서만 로깅
    }
}
```

```kotlin
// flavor별 분기
val limit = when (BuildConfig.FLAVOR) {
    "free" -> 10
    "paid" -> Int.MAX_VALUE
    else -> 0
}
```

### 소스 세트 분기 {#source-set-branching}

같은 클래스의 **구현 자체를 variant별로 다른 파일로 제공**하는 방식입니다. Gradle은 `src/main/`에 더해 `src/{flavor}/`, `src/{buildType}/` 디렉터리를 자동으로 소스 세트로 인식하고, 빌드 시 해당 variant의 소스 세트를 `main`과 병합합니다.

```text
src/
  main/java/com/example/Analytics.kt      // 공통 (없어도 됨)
  free/java/com/example/Analytics.kt      // free 빌드에 들어가는 구현
  paid/java/com/example/Analytics.kt      // paid 빌드에 들어가는 구현
```

이때 같은 패키지·이름의 클래스가 `main`과 flavor 양쪽에 동시에 있으면 **중복 정의로 컴파일 에러**가 납니다. flavor별 구현을 둘 거라면 그 클래스는 `main`에 두지 않고 각 flavor에만 둡니다. 리소스(`res/`)나 `AndroidManifest.xml`도 같은 규칙으로 병합되며, 매니페스트는 충돌 시 우선순위 규칙에 따라 합쳐집니다.

### 두 방식의 선택 기준 {#choosing-branch-strategy}

- **런타임 분기**: 차이가 작고(값 하나, 플래그 하나) 같은 코드 흐름 안에서 갈릴 때. 코드가 모여 있어 가독성이 좋습니다.
- **소스 세트 분기**: 구현 전체가 다르거나, 한쪽에만 의존성(특정 SDK)이 있어 코드를 아예 분리해야 할 때. 한 flavor의 코드가 다른 flavor 바이너리에 섞이지 않습니다.

## 요약 {#summary}

> **TL;DR** — Build Variant는 `buildType`(어떻게 빌드하나: debug/release)과 `productFlavor`(어떤 제품인가: free/paid)의 곱으로 결정됩니다. variant별로 달라지는 값은 `buildConfigField`로 `BuildConfig`에 컴파일 타임 상수로 주입하며, `BuildConfig.DEBUG`/`BuildConfig.FLAVOR` 등을 코드에서 정적으로 읽습니다. 빌드별 동작 분기는 BuildConfig 값을 검사하는 런타임 분기와, `src/{flavor}/` 소스 세트로 구현 자체를 갈아끼우는 분기 두 가지가 있습니다.

1. **buildType과 product flavor**: variant = flavor × buildType. buildType은 빌드/패키징 방식(서명·축소·디버그), flavor는 제품 정체성(기능·식별자·리소스)을 담당한다.
2. **BuildConfig 주입**: Gradle이 생성하는 final 클래스에 `buildConfigField`로 variant별 상수를 주입한다. 컴파일 타임 상수라 release에서 데드 코드가 제거되지만, APK에 평문으로 남으므로 비밀 키에는 부적합하다.
3. **빌드별 분기**: 값 하나가 갈리면 `BuildConfig.DEBUG`/`FLAVOR`를 검사하는 런타임 분기, 구현 전체가 갈리면 `src/{flavor}/` 소스 세트로 파일을 교체하는 분기를 쓴다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) buildType과 product flavor의 차이는 무엇인가요?">

buildType은 "같은 앱을 어떻게 빌드/패키징하는가"를 정의합니다. 기본으로 `debug`(디버그 서명·`debuggable`), `release`(코드 축소·릴리스 서명)가 있으며, 기능 차이보다 컴파일·패키징 설정에 관여합니다.

product flavor는 "같은 코드 베이스에서 만드는 서로 다른 제품 버전"을 정의합니다. 무료/유료, 고객사 A/B처럼 기능·리소스·applicationId가 갈리는 변종을 표현하며 `flavorDimensions` 차원에 속합니다.

최종 Build Variant는 `flavor × buildType`의 조합입니다. flavor가 free/paid, buildType이 debug/release면 freeDebug·freeRelease·paidDebug·paidRelease 4개가 만들어집니다.

</def>
<def title="Q) BuildConfig는 무엇이고, 커스텀 값은 어떻게 넣나요?">

`BuildConfig`는 Gradle이 빌드 시 자동 생성하는 final 클래스로, `DEBUG`·`APPLICATION_ID`·`BUILD_TYPE`·`FLAVOR`·`VERSION_NAME` 등을 컴파일 타임 상수로 제공합니다.

커스텀 값은 `buildConfigField("타입", "이름", "값")`으로 buildType이나 flavor 블록에 선언합니다. 세 번째 인자는 소스에 그대로 박히는 리터럴이라 문자열은 `"\"...\""`처럼 따옴표까지 직접 넣어야 합니다. AGP 8.0+에서는 `buildFeatures { buildConfig = true }`로 생성을 명시적으로 켜야 합니다.

이렇게 하면 API base URL이나 기능 플래그를 코드 수정 없이 variant별로 다르게 줄 수 있습니다.

</def>
<def title="Q) release 빌드에서 if (BuildConfig.DEBUG) 블록은 어떻게 되나요?">

`BuildConfig.DEBUG`는 컴파일 타임에 확정되는 `static final boolean` 상수입니다. release 빌드에서는 이 값이 false로 고정되므로 `if (BuildConfig.DEBUG) { ... }` 블록은 항상 거짓인 조건이 됩니다.

R8/ProGuard는 release 빌드에서 이런 도달 불가능한 가지를 데드 코드로 제거합니다. 따라서 디버그 전용 로깅·디버깅 코드가 릴리스 바이너리에 아예 포함되지 않아 용량과 코드 노출 면에서 유리합니다.

</def>
<def title="Q) 소스 세트(source set) 분기는 런타임 분기와 어떻게 다른가요?">

런타임 분기는 `if (BuildConfig.FLAVOR == "free")`처럼 한 파일 안에서 값으로 갈리는 방식입니다. 코드가 모여 있어 추적이 쉽고 값 하나가 달라지는 작은 차이에 적합합니다.

소스 세트 분기는 구현 자체를 variant별 디렉터리로 분리하는 방식입니다. `src/free/`, `src/paid/`에 같은 이름의 클래스를 각각 두면, Gradle이 빌드 시 해당 variant의 소스 세트를 `main`과 병합해 그 구현만 컴파일에 포함합니다.

구현 전체가 다르거나 한쪽에만 특정 의존성이 필요할 때 소스 세트 분기를 씁니다. 단, 같은 패키지·이름 클래스를 `main`과 flavor에 동시에 두면 중복 정의로 컴파일이 깨지므로, flavor별로 둘 클래스는 `main`에 두지 않습니다.

</def>
<def title="Q) buildConfigField에 API 비밀 키를 넣어도 되나요?">

권장하지 않습니다. `buildConfigField`로 넣은 값은 컴파일 타임 상수로 BuildConfig 클래스에 박혀 APK 안에 평문으로 남습니다. 디컴파일하면 그대로 노출되므로 실제 비밀 키에는 부적합합니다.

API base URL이나 기능 플래그처럼 노출돼도 위험하지 않은 구성 값에는 적합합니다. 진짜 비밀은 서버 측에 두거나, NDK·암호화 저장소·런타임 발급(서버에서 토큰 발급) 같은 별도 보안 수단을 써야 합니다. BuildConfig는 비밀 보관소가 아니라 빌드 구성 주입 수단으로 봐야 합니다.

</def>
</deflist>
