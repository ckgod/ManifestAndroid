# Q25) Build Variants, Flavors

## Build Variant 및 Flavor란 무엇인가요? {#BVF131}

[Build Variant 및 Flavor](https://developer.android.com/build/build-variants)는 단일 codebase에서 애플리케이션의 여러 버전을 생성하는 유연한 방법을 제공합니다. 
이 시스템을 통해 개발자는 개발 및 프로덕션 빌드, 또는 무료 및 유료 버전과 같은 여러 구성을 동일한 프로젝트 내에서 효율적으로 관리할 수 있습니다.

### Build Variant

A Build Variant는 특정 Build Type과 Product Flavor(Flavor가 정의된 경우)를 결합한 결과입니다.
Android Gradle Plugin은 각 조합에 대해 Build Variant를 생성하여 다양한 사용 사례에 맞춰진 APK 또는 Bundle을 생성할 수 있도록 합니다.

Build Type은 애플리케이션이 빌드되는 방식을 나타내며, 일반적으로 다음을 포함합니다:

*   **Debug**: 개발 중에 사용되는 빌드 구성입니다. 일반적으로 디버그 도구, 로그 및 테스트를 위한 디버그 certificate를 포함합니다.
*   **Release**: 배포에 최적화된 구성으로, 종종 minification, obfuscation이 적용되고 스토어 게시를 위한 release key로 서명됩니다.

기본적으로 모든 Android project에는 `debug` 및 `release` Build Type이 포함됩니다.
개발자는 특정 요구 사항에 맞춰 Custom Build Type을 추가할 수 있습니다.

### Product Flavor

Product Flavor는 개발자가 앱의 다양한 변형을 정의할 수 있도록 합니다.
예를 들어, 무료 버전과 유료 버전, 또는 `us` 및 `eu`와 같은 지역별 버전이 있습니다.
각 Flavor는 application ID, version name 또는 resources와 같은 고유한 구성을 가질 수 있습니다.
이를 통해 코드 중복 없이 맞춤형 빌드를 쉽게 만들 수 있습니다.

Flavor가 있는 일반적인 `build.gradle` 구성은 다음과 같습니다:

```groovy
android {
    // ...
    flavorDimensions = "version"

    productFlavors {
        free {
            applicationId = "com.example.app.free"
            versionName = "1.0-free"
        }

        paid {
            applicationId = "com.example.app.paid"
            versionName = "1.0-paid"
        }
    }
}
```

이 설정으로 Android Gradle Plugin은 `freeDebug`, `freeRelease`, `paidDebug`, `paidRelease`와 같은 조합을 생성합니다.

### Build Type과 Flavor 결합

Build Variant 시스템은 Build Type과 Product Flavor를 결합하여 잠재적인 Build의 matrix를 생성합니다.
예를 들면 다음과 같습니다:

*   `freeDebug`: 디버깅을 위한 무료 버전
*   `paidRelease`: 릴리스에 최적화된 유료 버전

각 조합은 특정 구성, resources 또는 code를 가질 수 있습니다.
예를 들어, 무료 버전에서는 광고를 표시하고 유료 버전에서는 광고를 비활성화할 수 있습니다.
Flavor-specific resource directories 또는 Java/Kotlin code를 사용할 수 있습니다.

### Build Variant 및 Flavor 사용의 장점

1.  **효율적인 Configuration Management**: 중복을 줄이고 단일 codebase에서 여러 Build를 처리할 수 있습니다.
2.  **Custom Behavior**: 유료 버전에서 premium features를 활성화하거나 `debug` 및 `release` Build에 다른 APIs를 사용하는 등 앱 동작을 맞춤 설정할 수 있습니다.
3.  **Automation**: Gradle은 variant에 따라 APK signing, shrinking, obfuscation과 같은 작업을 자동화합니다.

### 요약

Android의 Build Variant는 Build Type과 Product Flavor를 결합하여 맞춤형 앱 Build를 생성합니다.
Build Type은 앱이 빌드되는 방식에 대한 구성(예: `debug` vs. `release`)을 정의하고, Product Flavor는 앱의 변형(예: 무료 vs. 유료)을 정의합니다.
이 둘은 함께 여러 앱 configurations를 관리하는 유용한 시스템을 생성하여 개발 및 배포의 효율성과 scalability를 보장합니다.

> Q) Build Type과 Product Flavor의 차이점은 무엇이며, Build Variant를 생성하기 위해 어떻게 함께 작동하나요?