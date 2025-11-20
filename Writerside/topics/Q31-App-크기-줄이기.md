# Q31) 앱 크기 줄이기

## 애플리케이션 크기를 어떻게 줄일 수 있나요?
Android 애플리케이션의 크기를 최적화하는 것은 특히 기기 저장 공간이 제한적이거나 인터넷 연결 속도가 느린 사용자에게 사용자 경험을 개선하는 데 필수적입니다.
기능을 저해하지 않으면서 애플리케이션 크기를 줄이기 위해 여러 전략을 사용할 수 있습니다.

### 사용하지 않는 리소스 제거

이미지, 레이아웃, 문자열과 같이 사용되지 않는 리소스는 `APK` 또는 `AAB` 크기를 불필요하게 늘립니다. 
`Android Studio`의 `Lint`와 같은 도구는 이러한 리소스를 식별하는 데 도움을 줄 수 있습니다. 
사용하지 않는 리소스를 제거한 후 `build.gradle` 파일에서 `shrinkResources`를 활성화하여 빌드 프로세스 중에 사용하지 않는 리소스를 자동으로 제거합니다.

```groovy
android {
    buildTypes {
        release {
            minifyEnabled true
            shrinkResources true
        }
    }
}
```

### `R8`로 코드 축소 활성화

`Android`의 기본 코드 축소기 및 최적화 도구인 `R8`은 사용하지 않는 클래스와 메서드를 제거합니다.
또한 코드를 난독화하여 더욱 압축합니다. 적절한 `ProGuard` 규칙은 중요한 코드나 리플렉션 기반 라이브러리가 제거되지 않도록 보장합니다.

```groovy
android {
    buildTypes {
        release {
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

### 리소스 최적화 사용

이미지 및 XML 파일과 같은 리소스를 최적화하면 앱 크기를 크게 줄일 수 있습니다.
*   **Vector Drawables**: 래스터 이미지(예: `PNG`, `JPEG`)를 `vector drawables`로 대체하여 공간을 적게 차지하면서도 확장 가능한 그래픽을 사용합니다.
*   **이미지 압축**: `TinyPNG` 또는 `ImageMagick`와 같은 도구를 사용하여 눈에 띄는 품질 손실 없이 래스터 이미지를 압축합니다.
*   **WebP Format**: 이미지를 `WebP` 형식으로 변환합니다. `WebP`는 `PNG` 또는 `JPEG`보다 더 나은 압축률을 제공합니다.

```groovy
android {
    defaultConfig {
        vectorDrawables.useSupportLibrary = true
    }
}
```

### `Android App Bundles (AAB)` 사용

`Android App Bundle (AAB)` 형식으로 전환하면 `Google Play`가 개별 기기에 최적화된 `APK`를 제공할 수 있습니다. 
이는 특정 구성(예: 화면 밀도, `CPU` 아키텍처 또는 언어)에 필요한 리소스와 코드만 포함하여 앱 크기를 줄입니다.

```groovy
android {
    bundle {
        density {
            enableSplit true
        }
        abi {
            enableSplit true
        }
        language {
            enableSplit true
        }
    }
}
```

### 불필요한 종속성 제거

프로젝트의 종속성을 검토하고 사용하지 않거나 중복되는 라이브러리를 제거합니다.
`Android Studio`의 [Gradle Dependency Analyzer](https://www.jetbrains.com/help/idea/work-with-gradle-dependency-diagram.html#dependency_analyzer)를 사용하여 무거운 라이브러리와 전이적 종속성을 식별할 수 있습니다.

### 네이티브 라이브러리 최적화

앱에 네이티브 라이브러리가 포함된 경우, 다음 전략을 사용하여 그 영향을 줄입니다.
*   **사용하지 않는 아키텍처 제외**: `build.gradle` 파일의 `abiFilters` 옵션을 사용하여 필요한 `ABI`만 포함합니다.
*   **디버그 심볼 제거**: `stripDebugSymbols`를 사용하여 네이티브 라이브러리에서 디버깅 심볼을 제거합니다.

```groovy
android {
    defaultConfig {
        ndk {
            abiFilters "armeabi-v7a", "arm64-v8a" // 필요한 ABI만 포함
        }
    }
    packagingOptions {
        exclude "**/lib/**/*.so.debug"
    }
}
```

### `ProGuard` 규칙 구성을 통한 디버그 정보 축소

디버깅 메타데이터는 최종 `APK` 또는 `AAB`에 불필요한 무게를 더합니다.
`proguard-rules.pro` 파일을 구성하여 이러한 정보를 제거합니다.

```
-dontwarn com.example.unusedlibrary.**
-keep class com.example.important.** { *; }
```

### 동적 기능 사용

`Dynamic feature modules`를 사용하면 덜 자주 사용되는 기능을 온디맨드 모듈로 분리하여 앱을 모듈화할 수 있습니다. 
이렇게 하면 초기 다운로드 크기가 줄어듭니다.

```
dynamicFeatures = [":feature1", ":feature2"]
```

### 앱 내 대용량 에셋 피하기

*   비디오나 고해상도 이미지와 같은 대용량 에셋을 `CDN`에 호스팅하고 런타임에 동적으로 로드합니다.
*   앱에 미디어 콘텐츠를 함께 번들링하는 대신 스트리밍을 사용합니다.

## 요약

`Android` 애플리케이션 크기를 줄이는 것은 사용하지 않는 리소스 제거, 코드 축소를 위한 `R8` 활성화, 리소스 최적화, `App Bundles`와 같은 최신 형식 활용을 포함한 여러 전략의 조합을 필요로 합니다. 
또한 종속성을 면밀히 검토하고, 네이티브 라이브러리를 최적화하며, 기능을 모듈화하면 앱 크기를 더욱 최소화할 수 있습니다. 
이러한 관행은 가볍고 성능이 뛰어난 애플리케이션을 보장하여 탁월한 사용자 경험을 제공합니다.

> Q) 앱에 `APK`/`AAB` 크기를 크게 늘리는 고해상도 이미지가 포함되어 있습니다. 시각적 품질을 유지하면서 이미지 리소스를 어떻게 최적화하고, 최대 효율성을 위해 어떤 형식을 사용하시겠습니까?
>
> Q) 애플리케이션에 여러 기능이 포함되어 있지만, 일부는 대부분의 사용자가 거의 사용하지 않습니다. 필요할 때 해당 기능을 계속 사용할 수 있도록 하면서 초기 앱 크기를 줄이는 솔루션을 어떻게 구현하시겠습니까?