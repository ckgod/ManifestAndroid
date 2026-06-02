# Q68) KSP와 어노테이션 프로세싱

## 어노테이션 프로세싱이란 {#what-is-annotation-processing}

어노테이션 프로세싱(annotation processing)은 **컴파일 시점에 소스 코드의 어노테이션을 읽어, 추가 코드를 생성하거나 코드를 검증하는 메커니즘**입니다. 런타임 리플렉션과 대비되는 개념입니다.

안드로이드에서 흔히 쓰는 다음 라이브러리들이 모두 어노테이션 프로세서를 사용합니다.

- **Room**: `@Entity`, `@Dao`, `@Query`를 읽어 SQL 검증과 DAO 구현체를 생성합니다.
- **Dagger/Hilt**: `@Inject`, `@Module`을 읽어 의존성 그래프 코드를 생성합니다.
- **Moshi**: `@JsonClass`를 읽어 리플렉션 없는 JSON 어댑터를 생성합니다.

이 프로세서들이 **무엇을 입력으로 받아, 언제, 어떤 방식으로 코드를 만들어 내는가**가 이 토픽의 핵심입니다. KAPT와 KSP는 같은 목적(어노테이션 처리)을 서로 다른 메커니즘으로 달성하며, 그 차이가 빌드 성능을 가릅니다.

## 컴파일타임 코드 생성 {#compile-time-codegen}

### 런타임 리플렉션 대신 컴파일타임에 만드는 이유 {#why-compile-time}

같은 일을 두 시점에 할 수 있습니다.

- **런타임 리플렉션**: 앱 실행 중에 `Class`, 필드, 어노테이션을 조회해 동적으로 처리합니다. 작성은 간단하지만, 리플렉션 호출 비용이 들고, 잘못된 어노테이션 사용이 **런타임에 가서야** 크래시로 드러납니다.
- **컴파일타임 코드 생성**: 빌드 시점에 어노테이션을 읽어 일반 소스 코드(`.kt`/`.java`)를 미리 만들어 둡니다. 생성된 코드는 보통의 코드처럼 컴파일·인라인되므로 런타임 리플렉션 비용이 없고, 어노테이션 오류를 **컴파일 에러로** 즉시 잡습니다.

Room이 `@Query("SELECT * FROM user WHERE id = :id")`의 SQL 문법과 컬럼명을 컴파일 시점에 검증하고, 잘못되면 빌드를 실패시키는 것이 후자의 대표 사례입니다.

### 코드 생성의 동작 단계 {#codegen-steps}

어노테이션 프로세서는 컴파일러가 실행하는 플러그인입니다. 대략 다음 단계로 동작합니다.

1. 컴파일러가 소스를 파싱해 **심볼 정보**(클래스·함수·프로퍼티·어노테이션)를 만든다.
2. 등록된 프로세서에게 그 심볼을 넘긴다.
3. 프로세서는 대상 어노테이션이 붙은 심볼을 찾아 **새 소스 파일을 생성**한다.
4. 생성된 파일은 다시 컴파일 입력으로 들어가 함께 컴파일된다.

KAPT와 KSP의 차이는 바로 **1번에서 프로세서에게 무엇을, 어떤 형태로 넘기느냐**에 있습니다. 코드 생성 자체는 보통 [KotlinPoet](https://square.github.io/kotlinpoet/)이나 JavaPoet 같은 라이브러리로 `.kt`/`.java` 문자열을 조립해 출력합니다.

```kotlin
// 프로세서가 만들어 내는 결과물의 예 (Room이 생성하는 DAO 구현 골격)
class UserDao_Impl(private val db: RoomDatabase) : UserDao {
    override fun getById(id: Int): User {
        // 프로세서가 @Query 문자열을 검증한 뒤 채워 넣은 코드
        val sql = "SELECT * FROM user WHERE id = ?"
        // ... 커서를 읽어 User로 매핑하는 코드 ...
    }
}
```

## KAPT의 동작 메커니즘 {#how-kapt-works}

### KAPT는 자바 도구라는 점이 핵심 {#kapt-is-java-tool}

KAPT(Kotlin Annotation Processing Tool)는 **자바 표준 어노테이션 프로세싱 API(JSR 269, `javax.annotation.processing`)를 Kotlin에서 쓸 수 있게 해 주는 어댑터**입니다. 즉 프로세서 자체는 자바용으로 작성된 `javac` 프로세서입니다.

문제는 자바 프로세서가 **자바 타입 모델(`Element`, `TypeMirror`)만 이해한다**는 점입니다. Kotlin 소스를 그대로는 못 읽습니다. 그래서 KAPT는 중간 변환 단계를 둡니다.

### 스텁(stub) 생성 단계 {#kapt-stub-generation}

KAPT의 동작은 다음과 같습니다.

1. Kotlin 컴파일러가 모든 Kotlin 소스의 **심볼을 해석(resolve)** 한다.
2. 그 결과로 본문이 비어 있는 **자바 스텁(stub) 파일**을 생성한다. 시그니처와 어노테이션만 담긴 가짜 `.java`입니다.
3. 그 스텁을 입력으로 **자바 어노테이션 프로세서(`javac` apt)** 를 실행한다.
4. 프로세서가 생성한 코드를 다시 Kotlin/Java 컴파일에 합친다.

```kotlin
// 원본 Kotlin
@Entity data class User(@PrimaryKey val id: Int, val name: String)
```

위 코드를 처리하려면 KAPT는 먼저 아래와 같은 자바 스텁을 만들어야 합니다.

```java
// KAPT가 생성하는 자바 스텁 (본문 없음, 시그니처와 어노테이션만)
@Entity
public final class User {
    @PrimaryKey private final int id = 0;
    private final String name = null;
    public final int getId() { return 0; }     // 본문은 더미
    public final String getName() { return null; }
}
```

**2번의 스텁 생성이 KAPT 성능 비용의 핵심**입니다. 스텁을 만들려면 프로그램의 모든 심볼을 해석해야 하고, 이 비용은 전체 `kotlinc` 분석의 대략 1/3에 달합니다. 게다가 자바 스텁으로 내려가는 과정에서 Kotlin 고유 정보(널 가능성, `data class`, suspend 함수, 기본 인자 등)가 자바 모델에 맞춰 손실됩니다.

## KAPT vs KSP {#kapt-vs-ksp}

### KSP는 Kotlin 심볼을 직접 읽는다 {#ksp-reads-kotlin}

KSP(Kotlin Symbol Processing)는 구글이 만든 **Kotlin 네이티브 어노테이션 처리 API**입니다. 핵심 차이는 단 하나로 요약됩니다.

> KAPT는 Kotlin을 자바 스텁으로 번역한 뒤 자바 프로세서에 넘긴다. KSP는 Kotlin 컴파일러 플러그인으로서 **Kotlin 심볼을 자바를 거치지 않고 직접 프로세서에 넘긴다.**

KSP는 Kotlin 컴파일러 플러그인으로 동작하므로 **스텁 생성 단계가 아예 없습니다.** 프로세서는 자바 `Element` 대신 `KSClassDeclaration`, `KSFunctionDeclaration` 같은 **Kotlin 친화적 추상화**를 받습니다. 그래서 널 가능성, 확장 함수, 프로퍼티 같은 Kotlin 고유 개념을 손실 없이 다룰 수 있습니다.

```kotlin
// KSP 프로세서가 심볼을 다루는 모습
class MyProcessor(private val codeGenerator: CodeGenerator) : SymbolProcessor {
    override fun process(resolver: Resolver): List<KSAnnotated> {
        val symbols = resolver.getSymbolsWithAnnotation("com.example.MyAnnotation")
        symbols.filterIsInstance<KSClassDeclaration>().forEach { decl ->
            // decl.simpleName, decl.getAllProperties() 등 Kotlin 모델을 직접 사용
            generateCode(decl)
        }
        return emptyList()  // 이번 라운드에 처리하지 못한 심볼을 반환(다음 라운드로 연기)
    }
}
```

### 두 방식의 비교 {#kapt-ksp-comparison}

| 구분 | KAPT | KSP |
|------|------|------|
| 정체 | 자바 apt(JSR 269) 어댑터 | Kotlin 컴파일러 플러그인 |
| 입력 모델 | 자바 `Element`/`TypeMirror` | Kotlin `KSDeclaration` 등 |
| 자바 스텁 생성 | 필요 (비용의 핵심) | 불필요 |
| Kotlin 고유 정보 | 자바 모델로 손실 | 그대로 보존 |
| 프로세서 호환성 | 기존 자바 프로세서 그대로 | KSP용으로 새로 작성 필요 |
| 빌드 속도 | 느림 | 최대 약 2배 빠름 |

KSP의 한계는 **기존 자바 프로세서를 그대로 쓸 수 없다**는 점입니다. 라이브러리가 KSP를 지원하도록 별도 구현을 제공해야 합니다. 다만 Room, Hilt, Moshi, Glide 등 주요 라이브러리는 이미 KSP를 지원하므로, 실무에서는 대부분 KSP로 전환할 수 있습니다.

## 빌드 성능 {#build-performance}

### 왜 KSP가 빠른가 {#why-ksp-is-faster}

성능 차이의 원인은 **자바 스텁 생성 단계의 유무**입니다.

- KAPT는 처리 대상 어노테이션이 하나라도 있으면, 그 모듈의 Kotlin 심볼을 모두 해석해 자바 스텁을 만들어야 합니다. 이 스텁 생성이 전체 분석 비용의 약 1/3을 차지합니다.
- KSP는 스텁 없이 Kotlin 컴파일러가 만든 심볼을 곧바로 읽으므로 이 비용이 통째로 사라집니다.

실측 사례로, Tachiyomi 프로젝트에서 동일한 처리를 KAPT는 코드 생성에 약 8.67초가 걸린 반면 KSP 구현은 약 1.15초만 걸렸습니다. 구글은 KSP가 KAPT 대비 최대 약 2배 빠르다고 밝히고 있습니다.

### 점진 전환 시 주의점 {#migration-caveat}

KAPT와 KSP는 한 프로젝트에서 **공존할 수 있습니다.** 다만 성능상 함정이 하나 있습니다.

> 한 모듈에 KAPT 프로세서가 **하나라도 남아 있으면**, 그 모듈은 여전히 자바 스텁을 생성합니다. 따라서 스텁 생성 비용을 없애려면 **해당 모듈의 KAPT를 전부 제거**해야 합니다. 일부만 KSP로 바꾸면 성능 이득이 거의 없습니다.

빌드 스크립트에서는 `kapt` 플러그인 대신 `ksp` 플러그인을 적용하고, 의존성 설정 키워드도 바꿉니다.

```kotlin
// build.gradle.kts — KAPT
plugins { id("org.jetbrains.kotlin.kapt") }
dependencies {
    kapt("androidx.room:room-compiler:2.6.1")
}

// build.gradle.kts — KSP로 전환
plugins { id("com.google.devtools.ksp") }
dependencies {
    ksp("androidx.room:room-compiler:2.6.1")
}
```

### 증분 처리(incremental processing)도 빌드 시간에 영향 {#incremental-processing}

KSP는 **증분 처리**를 기본 지원합니다. 일부 파일만 바뀌었을 때 영향받는 파일만 다시 처리하므로, 매번 전체를 다시 도는 것보다 재빌드가 빠릅니다. KAPT도 증분 처리를 지원하지만, 자바 스텁 단계가 끼어 있어 KSP보다 효율이 떨어집니다. 결과적으로 클린 빌드와 증분 빌드 양쪽에서 KSP가 유리합니다.

## 요약 {#summary}

> **TL;DR** — 어노테이션 프로세싱은 컴파일 시점에 어노테이션을 읽어 코드를 생성·검증하는 메커니즘으로, 런타임 리플렉션 비용과 런타임 오류를 없애 줍니다. KAPT는 Kotlin을 자바 스텁으로 번역한 뒤 자바 프로세서를 돌리는데, 이 스텁 생성이 전체 분석의 약 1/3을 차지해 느립니다. KSP는 Kotlin 컴파일러 플러그인으로서 스텁 없이 Kotlin 심볼을 직접 읽어 최대 약 2배 빠르며, 단 한 모듈에 KAPT가 하나라도 남으면 스텁 비용이 유지됩니다.

1. **컴파일타임 코드 생성**: 빌드 시점에 어노테이션을 읽어 일반 소스를 미리 생성한다. 런타임 리플렉션 비용이 없고 오류를 컴파일 에러로 잡는다.
2. **KAPT vs KSP**: KAPT는 자바 apt 어댑터라 Kotlin을 자바 스텁으로 번역해 자바 프로세서에 넘긴다. KSP는 Kotlin 컴파일러 플러그인이라 스텁 없이 Kotlin 심볼을 직접 읽고, Kotlin 고유 정보도 보존한다.
3. **빌드 성능**: 성능 차이의 근원은 자바 스텁 생성 단계의 유무다. KSP는 그 단계가 없어 최대 약 2배 빠르며, 모듈에서 KAPT를 완전히 제거해야 이득이 온전히 실현된다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 어노테이션 프로세싱이란 무엇이고, 런타임 리플렉션 대신 쓰면 어떤 이점이 있나요?">

어노테이션 프로세싱은 컴파일 시점에 소스의 어노테이션을 읽어 추가 코드를 생성하거나 코드를 검증하는 메커니즘입니다. Room, Hilt, Moshi 같은 라이브러리가 모두 이 방식을 씁니다.

런타임 리플렉션과 비교하면 두 가지 이점이 있습니다. 첫째, 코드를 미리 생성해 두므로 실행 중 리플렉션 호출 비용이 없습니다. 생성된 코드는 보통 코드처럼 컴파일·최적화됩니다. 둘째, 어노테이션의 잘못된 사용을 런타임이 아니라 컴파일 시점에 에러로 잡습니다. 예를 들어 Room은 `@Query`의 SQL 문법과 컬럼명을 빌드 시점에 검증해 틀리면 빌드를 실패시킵니다.

</def>
<def title="Q) KAPT는 내부적으로 어떻게 동작하나요? 왜 자바 스텁을 만드나요?">

KAPT는 자바 표준 어노테이션 처리 API(JSR 269)를 Kotlin에서 쓰게 해 주는 어댑터입니다. 실제 프로세서는 자바용으로 작성된 `javac` 프로세서이고, 이들은 자바 타입 모델(`Element`, `TypeMirror`)만 이해합니다.

그런데 자바 프로세서는 Kotlin 소스를 직접 못 읽습니다. 그래서 KAPT는 먼저 Kotlin 컴파일러로 모든 심볼을 해석한 뒤, 시그니처와 어노테이션만 담긴 본문 없는 자바 스텁 파일을 생성합니다. 그 스텁을 입력으로 자바 프로세서를 돌리고, 생성된 코드를 다시 컴파일에 합칩니다. 이 스텁을 만드는 이유는 자바 프로세서에게 줄 자바 형태의 입력이 필요하기 때문이며, 이 단계가 KAPT 성능 비용의 핵심입니다.

</def>
<def title="Q) KSP가 KAPT보다 빠른 이유를 메커니즘 수준에서 설명해 주세요.">

성능 차이의 근원은 자바 스텁 생성 단계의 유무입니다. KAPT는 자바 프로세서에게 넘길 자바 스텁을 만들어야 하는데, 스텁을 만들려면 프로그램의 모든 심볼을 해석해야 하고 이 비용이 전체 `kotlinc` 분석의 약 1/3에 달합니다.

KSP는 Kotlin 컴파일러 플러그인으로 동작하므로 스텁 단계가 아예 없습니다. 컴파일러가 만든 Kotlin 심볼을 `KSClassDeclaration` 같은 Kotlin 친화적 추상화로 곧바로 받아 처리합니다. 자바로 내려갔다 올라오는 왕복이 없어지므로 그만큼 빨라지고, 구글은 최대 약 2배 빠르다고 밝힙니다. 부수적으로 KSP는 증분 처리도 기본 지원해 재빌드도 더 빠릅니다.

</def>
<def title="Q) KAPT에서 KSP로 전환할 때 주의할 점은 무엇인가요?">

가장 중요한 함정은, 한 모듈에 KAPT 프로세서가 하나라도 남아 있으면 그 모듈은 여전히 자바 스텁을 생성한다는 점입니다. 따라서 일부 프로세서만 KSP로 바꾸면 스텁 비용이 그대로 남아 성능 이득이 거의 없습니다. 모듈 단위로 KAPT를 완전히 제거해야 성능 개선이 실현됩니다.

또 하나는 호환성입니다. KSP는 기존 자바 프로세서를 그대로 쓸 수 없고, 라이브러리가 KSP용 구현을 제공해야 합니다. 다행히 Room, Hilt, Moshi, Glide 등 주요 라이브러리는 이미 KSP를 지원합니다. 빌드 스크립트에서는 `kapt` 플러그인과 `kapt(...)` 의존성을 `ksp` 플러그인과 `ksp(...)` 의존성으로 교체하면 됩니다.

</def>
<def title="Q) KSP가 Kotlin 고유 정보를 손실 없이 다룰 수 있는 이유는 무엇인가요?">

KAPT는 Kotlin을 자바 스텁으로 번역하는 과정에서 자바 타입 모델에 없는 Kotlin 개념이 손실됩니다. 널 가능성, `data class`, suspend 함수, 기본 인자, 확장 함수 같은 정보가 자바 모델에 맞춰 깎이거나 사라집니다.

KSP는 자바를 거치지 않고 Kotlin 컴파일러의 심볼을 직접 읽습니다. 프로세서가 받는 추상화 자체가 `KSClassDeclaration`, `KSFunctionDeclaration`처럼 Kotlin 모델을 그대로 반영하므로, 널 가능성이나 프로퍼티 같은 Kotlin 고유 개념을 손실 없이 조회할 수 있습니다. 그래서 Kotlin 전용 심볼을 다루는 라이브러리에서 KSP가 더 정확하게 동작합니다.

</def>
</deflist>
