# Q70) 앱 보안 - 시크릿 관리

안드로이드 앱은 사용자의 기기에 설치되는 순간 **공격자의 손에 들어간 클라이언트**가 됩니다. APK는 누구나 내려받아 `apktool`이나 `jadx` 같은 도구로 디컴파일할 수 있고, 실행 중 메모리는 루팅된 기기에서 덤프될 수 있습니다. 따라서 시크릿 관리의 출발점은 다음 사실을 인정하는 것입니다.

> **앱에 박힌 시크릿은 비밀이 아닙니다.** 클라이언트에 들어간 값은 추출 난이도를 높일 수 있을 뿐, 완전히 숨길 수는 없습니다.

이 토픽은 그 전제 위에서, (1) 진짜 비밀과 식별자를 구분해 다루는 법, (2) 빌드 시점에 키를 코드 밖으로 분리하고 형상관리에서 격리하는 법, (3) 릴리스 빌드에서 로깅·역공학 표면을 줄이는 법을 다룹니다.

## 무엇이 시크릿인가: 키 분류와 격리 {#secret-classification}

가장 먼저 해야 할 일은 "이 값이 클라이언트에 있어도 되는가"를 분류하는 것입니다.

| 분류 | 예시 | 클라이언트에 둬도 되는가 |
|------|------|--------------------------|
| 공개 식별자 | Google Maps API 키, OAuth client ID, Firebase `google-services.json` | 둘 수 있음 (단, 콘솔에서 사용처 제한 필수) |
| 진짜 비밀 | 결제 secret key, DB 비밀번호, 서버 마스터 토큰 | **절대 안 됨 — 서버에만** |

핵심 원칙은 **진짜 비밀은 클라이언트에 두지 않는다**입니다. 결제 승인, 외부 유료 API 호출 같은 민감 작업은 앱이 직접 시크릿으로 호출하지 말고, **백엔드를 프록시로 두고** 앱은 백엔드에만 인증하도록 설계합니다. 그래야 시크릿이 서버 밖으로 나가지 않습니다.

클라이언트에 둘 수밖에 없는 식별자(예: Maps API 키)는 **격리가 아니라 사용 제한으로** 보호합니다. Google Cloud Console에서 해당 키를 **패키지명 + SHA-1 서명 지문**으로 제한하면, 키가 유출돼도 다른 앱이 그 키로 호출할 수 없습니다. 즉 "키를 못 보게 하는 것"이 아니라 "봐도 못 쓰게 하는 것"이 클라이언트 키의 진짜 방어선입니다.

### 격리의 의미 {#isolation-meaning}

여기서 말하는 "API 키 격리"는 두 가지 층위를 가집니다.

1. **소스 코드로부터의 격리**: 키 문자열을 `.kt`/`.xml`에 하드코딩하지 않고 빌드 변수로 주입합니다. 하드코딩하면 git 히스토리와 디컴파일된 코드 양쪽에 남습니다.
2. **형상관리로부터의 격리**: 키가 담긴 파일을 git에 커밋하지 않습니다. 다음 두 섹션이 이 두 층위를 각각 다룹니다.

## local.properties와 .gitignore로 키를 빼내기 {#local-properties-gitignore}

안드로이드에서 키를 코드와 git 양쪽에서 분리하는 표준 방식은 **`local.properties`에 키를 적고, 빌드 시 `BuildConfig`로 주입**하는 것입니다.

`local.properties`는 원래 Android Studio가 SDK 경로(`sdk.dir`)를 저장하려고 만든 파일이며, **신규 프로젝트의 `.gitignore`에 기본으로 등록되어 있습니다.** 즉 처음부터 커밋되지 않는 파일이라, 개발자별 로컬 값을 두기에 적합합니다.

### 1단계: 키를 local.properties에 둔다 {#step-local-properties}

```properties
# local.properties (커밋되지 않음)
sdk.dir=/Users/me/Library/Android/sdk
MAPS_API_KEY=AIzaSyD-실제키값
```

### 2단계: .gitignore에 등록되어 있는지 확인한다 {#step-gitignore}

```text
# .gitignore
local.properties
```

이 한 줄이 **시크릿 격리의 핵심**입니다. 이 파일이 커밋되면 git 히스토리에 영구히 남고, 한 번 push된 키는 강제 회수(키 폐기 후 재발급) 외에는 되돌릴 방법이 없습니다. `git rm --cached`로 추적만 풀어도 과거 커밋에는 그대로 남아 있기 때문입니다.

### 3단계: build.gradle에서 읽어 BuildConfig로 주입한다 {#step-buildconfig}

```kotlin
// app/build.gradle.kts
import java.util.Properties

val localProps = Properties().apply {
    val f = rootProject.file("local.properties")
    if (f.exists()) f.inputStream().use { load(it) }
}

android {
    defaultConfig {
        // 따옴표까지 포함해야 String 리터럴이 된다
        buildConfigField(
            "String",
            "MAPS_API_KEY",
            "\"${localProps.getProperty("MAPS_API_KEY") ?: ""}\""
        )
    }
    buildFeatures {
        buildConfig = true   // AGP 8.0+ 에서는 명시적으로 켜야 한다
    }
}
```

```kotlin
// 코드에서 사용
val key = BuildConfig.MAPS_API_KEY
```

`AndroidManifest.xml`에 키가 필요한 경우(예: Maps)는 `manifestPlaceholders`로 같은 값을 흘려보냅니다.

```kotlin
defaultConfig {
    manifestPlaceholders["MAPS_API_KEY"] = localProps.getProperty("MAPS_API_KEY") ?: ""
}
```

```xml
<meta-data
    android:name="com.google.android.geo.API_KEY"
    android:value="${MAPS_API_KEY}" />
```

### 협업과 CI에서의 보완 {#collaboration-ci}

`local.properties`는 커밋되지 않으므로, 새 팀원이나 CI 빌드 머신에는 그 파일이 없습니다. 두 가지로 보완합니다.

- **예시 파일 커밋**: 키 값은 비운 `local.properties.example`을 커밋해 어떤 키가 필요한지 문서화합니다.
- **CI는 환경변수/시크릿 스토어 사용**: GitHub Actions라면 키를 레포지토리 Secret에 넣고, 빌드 스텝에서 `local.properties`를 생성하거나 `ORG_GRADLE_PROJECT_` 접두사 환경변수로 Gradle 프로퍼티를 주입합니다.

> `BuildConfig`로 주입한 키는 결국 컴파일된 바이트코드 안에 문자열로 들어갑니다. `local.properties`는 **git 유출과 소스 하드코딩을 막는 것**이지, 디컴파일로부터 키를 숨기는 수단이 아닙니다. 디컴파일 방어는 다음 섹션의 난독화와, 무엇보다 콘솔의 키 사용 제한이 담당합니다.

## 빌드 타입별 로깅과 난독화 {#build-logging-obfuscation}

릴리스 빌드는 디버그 빌드와 **보안 표면이 달라야** 합니다. 로그로 새는 정보와 역공학으로 읽히는 코드를 릴리스에서만 줄입니다.

### 빌드 타입별 로깅 차단 {#build-type-logging}

디버그 빌드에서 편하게 쓰던 `Log.d(...)`가 릴리스 APK에 그대로 남으면, 사용자가 `adb logcat`이나 로그 수집 도구로 토큰·응답 본문 같은 민감 정보를 볼 수 있습니다. 두 가지를 함께 씁니다.

**1) 빌드 타입으로 로깅 on/off를 분기**합니다. `BuildConfig.DEBUG`로 직접 가드하거나, 래퍼를 둡니다.

```kotlin
object Logger {
    fun d(tag: String, msg: String) {
        if (BuildConfig.DEBUG) Log.d(tag, msg)
    }
}
```

**2) R8/ProGuard로 로그 호출 자체를 제거**합니다. 릴리스 빌드에서 `Log` 호출을 바이트코드에서 통째로 들어내면, 가드를 깜빡한 호출도 안전해집니다.

```text
# proguard-rules.pro — 릴리스에서 Log.* 호출 제거
-assumenosideeffects class android.util.Log {
    public static int d(...);
    public static int v(...);
    public static int i(...);
}
```

`-assumenosideeffects`는 "이 메서드는 부작용이 없으니 반환값을 안 쓰면 호출을 지워도 된다"고 R8에 알리는 지시입니다. 단, 인자 계산에 부작용이 있으면(예: `Log.d(tag, expensiveCall())`) 호출은 지워져도 `expensiveCall()`은 남을 수 있으므로, 로그 인자에 부작용을 넣지 않는 습관이 함께 필요합니다.

### 난독화와 코드 축소: R8 {#r8-obfuscation}

**R8**은 현재 안드로이드 표준 빌드 도구로, ProGuard를 대체하며 다음 세 가지를 한 번에 수행합니다.

- **축소(shrinking)**: 도달 불가능한 클래스·메서드·필드를 제거합니다.
- **난독화(obfuscation)**: 클래스·메서드·필드 이름을 `a`, `b` 같은 짧은 이름으로 바꿔 디컴파일 결과의 가독성을 떨어뜨립니다.
- **최적화(optimization)**: 인라이닝 등으로 코드를 다듬습니다.

릴리스 빌드 타입에서만 켭니다.

```kotlin
// app/build.gradle.kts
android {
    buildTypes {
        release {
            isMinifyEnabled = true      // R8 (축소 + 난독화 + 최적화)
            isShrinkResources = true    // 미사용 리소스 제거
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
        getByName("debug") {
            isMinifyEnabled = false     // 디버그는 디버깅 편의 위해 끔
        }
    }
}
```

난독화가 보안에 기여하는 부분과 한계를 정확히 알아야 합니다.

- **기여**: 식별자 이름이 사라져 디컴파일된 코드의 의미 파악이 어려워지고, 미사용 코드가 제거돼 공격 표면이 줄어듭니다.
- **한계**: 난독화는 **암호화가 아닙니다.** 문자열 상수(API 키 포함)는 그대로 보이고, 로직은 여전히 추적 가능합니다. 따라서 난독화는 "추출 난이도를 높이는 보조 수단"이지, 시크릿을 숨기는 1차 방어선이 아닙니다.

### 진짜 비밀이 클라이언트에 있어야 한다면 {#native-keystore}

그래도 어떤 키를 클라이언트에 두고 추출 난이도를 더 높여야 한다면, 두 가지 보강책이 있습니다.

- **NDK로 C/C++ 코드에 숨기기**: 네이티브 라이브러리(`.so`)는 자바 디컴파일 도구로 한 번에 읽히지 않아, 평문 문자열보다 추출이 번거롭습니다. 단, `strings` 명령이나 동적 분석으로 여전히 추출 가능하므로 **지연 수단일 뿐**입니다.
- **민감 데이터 저장은 EncryptedSharedPreferences / Android Keystore**: 사용자별로 받아 저장하는 토큰 같은 값은 평문 `SharedPreferences` 대신 `Android Keystore`로 보호되는 저장소에 둡니다. 이는 "빌드에 박는 시크릿"이 아니라 "런타임에 받는 민감 데이터"의 문제이며, 키 자체가 기기 하드웨어 보안 영역(TEE/StrongBox)에 머무릅니다.

결론적으로, 클라이언트 측 시크릿 보호의 우선순위는 **① 진짜 비밀은 서버로 → ② 클라이언트 키는 콘솔에서 사용 제한 → ③ git·소스에서 격리 → ④ 릴리스 로깅 차단·난독화로 표면 축소** 순서입니다.

## 요약 {#summary}

> **TL;DR** — 앱에 박힌 시크릿은 디컴파일·메모리 덤프로 추출될 수 있으므로 "숨김"이 아니라 "분류·격리·표면 축소"로 접근합니다. 진짜 비밀(결제·DB)은 서버에 두고, 클라이언트에 둘 수밖에 없는 키는 콘솔에서 패키지명·서명 지문으로 사용을 제한합니다. 키 문자열은 `local.properties`(`.gitignore` 기본 등록)에 적어 `BuildConfig`로 주입해 소스·git에서 격리하고, 릴리스 빌드에서는 `-assumenosideeffects`로 `Log` 호출을 제거하고 R8(`isMinifyEnabled=true`)로 난독화·축소해 정보 노출과 역공학 표면을 줄입니다.

1. **키 분류와 격리**: 진짜 비밀은 클라이언트에 두지 않고 서버 프록시로 처리한다. 클라이언트에 둘 식별자는 콘솔의 패키지명+SHA-1 제한으로 "봐도 못 쓰게" 만든다.
2. **local.properties · .gitignore**: 키를 `local.properties`(기본적으로 `.gitignore`에 등록됨)에 두고 `build.gradle`에서 읽어 `BuildConfig`/`manifestPlaceholders`로 주입한다. 소스 하드코딩과 git 유출을 동시에 막는다.
3. **빌드별 로깅·난독화**: 릴리스에서 `BuildConfig.DEBUG` 가드 + `-assumenosideeffects`로 로그를 없애고, `isMinifyEnabled=true`로 R8 축소·난독화를 켠다. 난독화는 암호화가 아니라 추출 난이도를 높이는 보조 수단이다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) API 키를 BuildConfig로 주입하면 안전한가요? 그렇지 않다면 무엇을 위한 것인가요?">

`BuildConfig`로 주입한 키는 컴파일된 바이트코드 안에 문자열 상수로 들어가므로, APK를 디컴파일(`jadx` 등)하면 추출됩니다. 난독화를 켜도 문자열 상수는 그대로 보이므로 안전하지 않습니다.

`local.properties` + `BuildConfig` 방식이 실제로 막아 주는 것은 두 가지입니다. 첫째, 키를 `.kt`/`.xml`에 하드코딩하지 않게 해 소스에서 분리합니다. 둘째, `local.properties`가 `.gitignore`에 등록돼 있어 키가 git 히스토리에 커밋되는 것을 막습니다. 즉 이 방식은 "디컴파일로부터 숨김"이 아니라 "소스·형상관리로부터의 격리"가 목적입니다. 디컴파일에서 정말 보호해야 할 진짜 비밀은 애초에 클라이언트에 두지 말고 서버에 둬야 하고, 클라이언트에 둘 수밖에 없는 키는 콘솔에서 패키지명·서명 지문으로 사용을 제한해야 합니다.

</def>
<def title="Q) local.properties에 키를 두면 새 팀원이나 CI에서는 빌드가 깨집니다. 어떻게 처리하나요?">

`local.properties`는 `.gitignore`에 등록돼 커밋되지 않으므로, 새 머신에는 그 파일이 없습니다. `build.gradle`에서 키를 읽을 때 `getProperty(...) ?: ""`처럼 기본값을 줘 빌드 자체가 깨지지 않게 하고, 두 가지로 보완합니다.

협업용으로는 키 값을 비운 `local.properties.example`을 커밋해 어떤 키가 필요한지 문서화합니다. CI에서는 키를 GitHub Actions Secret 같은 시크릿 스토어에 넣고, 빌드 스텝에서 `local.properties`를 생성하거나 `ORG_GRADLE_PROJECT_` 접두사 환경변수로 Gradle 프로퍼티를 주입합니다. 핵심은 실제 키 값을 절대 레포지토리에 커밋하지 않고, 각 환경이 자기 경로(로컬 파일 / CI 시크릿)로 주입받게 하는 것입니다.

</def>
<def title="Q) 릴리스 빌드에서 Log 호출을 안전하게 제거하는 방법은 무엇인가요?">

두 층위를 함께 씁니다. 코드 레벨에서는 `if (BuildConfig.DEBUG) Log.d(...)`처럼 가드하거나 로깅 래퍼를 둬, 릴리스에서는 로그가 출력되지 않게 합니다. 빌드 레벨에서는 R8/ProGuard 규칙으로 호출 자체를 바이트코드에서 제거합니다.

```text
-assumenosideeffects class android.util.Log {
    public static int d(...);
    public static int v(...);
}
```

`-assumenosideeffects`는 해당 메서드가 부작용이 없다고 R8에 알려, 반환값을 쓰지 않는 호출을 통째로 제거하게 합니다. 이 규칙은 `isMinifyEnabled = true`로 R8이 켜진 릴리스 빌드에서만 적용됩니다. 주의할 점은 로그 인자 계산에 부작용이 있으면(예: 인자 안에서 상태를 바꾸는 호출) 그 인자 계산은 남을 수 있으므로, 로그 인자에 부작용을 넣지 않아야 한다는 것입니다.

</def>
<def title="Q) R8 난독화를 켜면 시크릿이 보호되나요? 난독화의 보안적 한계는 무엇인가요?">

부분적으로만, 그리고 직접적인 시크릿 보호 수단은 아닙니다. `isMinifyEnabled = true`로 켜는 R8은 축소(미사용 코드 제거)·난독화(이름을 `a`, `b`로 변경)·최적화를 수행합니다. 이로써 디컴파일 결과의 가독성이 떨어지고 공격 표면이 줄어드는 효과는 있습니다.

그러나 난독화는 암호화가 아닙니다. 식별자 이름은 바뀌어도 **문자열 상수(API 키 포함)는 그대로 노출**되고, 로직은 추적 가능합니다. 따라서 난독화는 "추출 난이도를 높이는 보조 수단"이지 시크릿을 숨기는 1차 방어선이 될 수 없습니다. 진짜 비밀은 서버에 두고, 클라이언트 키는 콘솔에서 사용을 제한하는 것이 본질적 방어이며, 난독화는 그 위에 얹는 보강책으로 이해해야 합니다.

</def>
<def title="Q) Maps API 키처럼 클라이언트에 둘 수밖에 없는 키는 어떻게 보호하나요?">

이런 키는 앱에 들어가는 순간 디컴파일로 추출 가능하므로, "숨김"이 아니라 "봐도 못 쓰게 하는" 사용 제한으로 보호합니다. Google Cloud Console에서 해당 키를 **애플리케이션 패키지명 + 앱 서명 SHA-1 지문**으로 제한하면, 키가 유출돼도 다른 패키지명·서명을 가진 앱이 그 키로 API를 호출할 수 없습니다. 추가로 키를 특정 API(예: Maps SDK)에만 쓰도록 API 제한도 겁니다.

병행해서, 키를 `local.properties`에 두고 `manifestPlaceholders`/`BuildConfig`로 주입해 소스 하드코딩과 git 커밋을 막고, 릴리스에서 R8 난독화로 추출 난이도를 더 높입니다. 정리하면 클라이언트 키 보호는 "콘솔 사용 제한(필수) + 소스·git 격리 + 난독화(보조)"의 조합입니다.

</def>
</deflist>
