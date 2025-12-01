# Q28) ART, Dalvik, Dex Compiler

## Android Runtime (ART), Dalvik, Dex Compiler란 무엇인가요?
Android 애플리케이션은 기기에서 실행되기 위해 고유한 런타임 환경과 컴파일 프로세스에 의존합니다.
[Android Runtime (ART), Dalvik, Dex Compiler](https://source.android.com/docs/core/runtime)는 이 프로세스에서 중요한 역할을 하여 앱이 성능, 메모리 효율성, Android 기기와의 호환성에 최적화되도록 보장합니다.

### Android Runtime (ART)
`Android Runtime (ART)`는 Android 4.4 (KitKat)에서 도입되어 Android 5.0 (Lollipop)부터 기본 런타임이 된 관리형 런타임 환경입니다. Dalvik을 대체하여 Android 앱을 실행하며 여러 개선 사항을 도입합니다.
ART는 Ahead-of-Time (AOT) compilation을 사용하여 애플리케이션을 컴파일하며, 앱 설치 중 bytecode를 machine code로 변환합니다.
이로 인해 런타임 시 Just-in-Time (JIT) compilation이 필요 없어 앱 시작 시간이 단축되고 실행 중 CPU 사용량이 줄어듭니다.

> Ahead-of-Time (AOT) compilation은 런타임 이전에 코드를 machine code로 컴파일하는 프로세스로, 실행 중 Just-In-Time (JIT) compilation의 필요성을 없앱니다. 이 접근 방식은 최적화된 precompiled binaries를 생성하여 성능을 향상시키고 런타임 오버헤드를 줄입니다.
>
> Just-In-Time (JIT) compilation은 bytecode가 실행 직전에 동적으로 machine code로 변환되는 런타임 프로세스입니다. 이를 통해 런타임 환경은 실제 실행 패턴에 따라 코드를 최적화하여 자주 사용되는 코드 경로의 성능을 향상시킬 수 있습니다.
{style="note"}

ART의 주요 특징은 다음과 같습니다:

*   **향상된 성능**: AOT compilation은 최적화된 machine code를 생성하여 런타임 오버헤드를 줄입니다.
*   **Garbage collection**: ART는 향상된 garbage collection 기술을 도입하여 더 나은 memory management를 제공합니다.
*   **Debugging 및 profiling 지원**: ART는 상세한 stack traces 및 memory usage analysis와 같은 개발자를 위한 향상된 도구를 제공합니다.

### Dalvik
Dalvik은 ART 이전에 Android에서 사용된 원래 런타임입니다. 
제한된 메모리와 처리 능력에 최적화하여 virtual machine 환경에서 애플리케이션을 실행하도록 설계되었습니다.

Dalvik은 Just-in-Time (JIT) compilation을 사용하여 런타임 시 bytecode를 machine code로 변환합니다.
이 접근 방식은 앱 설치에 필요한 시간을 줄이지만, 즉석 컴파일로 인해 런타임 오버헤드가 증가합니다.
Dalvik의 주요 특징은 다음과 같습니다:

*   **컴팩트한 bytecode**: Dalvik은 낮은 memory usage와 빠른 실행에 최적화된 .dex (Dalvik Executable) 파일을 사용합니다.
*   **Register-based VM**: Dalvik은 (Java Virtual Machine처럼) stack-based가 아닌 register-based로, instruction 효율성을 향상시킵니다.

느린 앱 시작 시간과 높은 CPU 사용량을 포함한 Dalvik의 한계로 인해 최신 Android 버전에서 ART로 대체되었습니다.

### Dex Compiler
Dex Compiler는 Java bytecode (Java/Kotlin compiler에 의해 생성됨)를 .dex (Dalvik Executable) 파일로 변환합니다. 이 .dex 파일은 Dalvik 및 ART 런타임 환경에 최적화된 컴팩트한 파일입니다.
Dex Compiler는 Android 애플리케이션이 기기에서 효율적으로 실행되도록 보장하는 데 중요한 역할을 합니다. Dex Compiler의 주요 특징은 다음과 같습니다:
*   **Multi-dex 지원**: 64K method limit을 초과하는 애플리케이션의 경우, Dex Compiler는 bytecode를 여러 .dex 파일로 분할하는 것을 지원합니다.
*   **Bytecode optimization**: 컴파일러는 Android 기기에서 더 나은 memory usage와 실행 성능을 위해 bytecode를 최적화합니다.

Dex compilation 프로세스는 Android build system에 통합되어 앱 개발의 build 단계에서 발생합니다.

### Dalvik에서 ART로의 전환
Dalvik에서 ART로의 전환은 Android 런타임 환경에서 상당한 개선을 가져왔습니다.
ART의 AOT compilation, 향상된 garbage collection, profiling capabilities는 더 나은 개발자 및 사용자 경험을 제공합니다.
Dalvik용으로 설계된 앱은 .dex 파일 사용 덕분에 ART와 완벽하게 호환되어 개발자에게 원활한 마이그레이션을 보장합니다.

### 요약
Android Runtime (ART), Dalvik, Dex Compiler는 Android에서 앱 실행의 기반을 형성합니다.
AOT compilation과 향상된 성능을 갖춘 ART는 JIT compilation에 의존했던 Dalvik을 대체했습니다.
Dex Compiler는 Java bytecode를 두 런타임 환경에 최적화된 .dex 파일로 변환하여 간극을 메웁니다.
이러한 구성 요소들은 함께 Android 기기에서 효율적이고 빠르며 안정적인 앱 실행을 보장합니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) ART의 Ahead-of-Time (AOT) compilation과 Dalvik의 Just-in-Time (JIT) compilation은 어떻게 다르며, 앱 시작 시간과 CPU 사용량에 어떤 영향을 미치나요?">

</def>
</deflist>
