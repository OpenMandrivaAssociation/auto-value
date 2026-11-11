Name:		auto-value
Version:	1.11.1
Release:	1
Summary:	Immutable value-type code generator
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/google/auto/tree/main/value
Source0:	https://github.com/google/auto/archive/refs/tags/auto-value-%{version}.tar.gz#/auto-value-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	mvn(com.google.guava:guava)
BuildRequires:	mvn(com.squareup:javapoet)
BuildRequires:	mvn(com.google.auto:auto-common)
BuildRequires:	mvn(com.google.escapevelocity:escapevelocity)
BuildRequires:	mvn(net.ltgt.gradle.incap:incap)
BuildRequires:	mvn(com.google.auto.service:auto-service-annotations)
BuildRequires:	mvn(com.google.errorprone:error_prone_annotations)
BuildRequires:	mvn(org.ow2.asm:asm)

%description
AutoValue %{version} generates immutable value classes. The annotations
and the processor are separate jars. OpenCensus uses the processor, so
this package does not stop at the annotation classes.

%prep
%autosetup -n auto-auto-value-%{version} -p1
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete

%build
JAVA=value/src/main/java/com/google/auto/value
find "$JAVA" -maxdepth 1 -name '*.java' ! -name 'module-info.java' > ann-sources.list
find "$JAVA/extension" -maxdepth 1 -name '*.java' >> ann-sources.list
find "$JAVA/extension/memoized" -maxdepth 1 -name '*.java' >> ann-sources.list
find "$JAVA/extension/serializable" -maxdepth 1 -name '*.java' >> ann-sources.list
find "$JAVA/extension/toprettystring" -maxdepth 1 -name '*.java' >> ann-sources.list
test "$(wc -l < ann-sources.list)" -eq 8
mkdir -p ann-classes
javac --release 11 -encoding UTF-8 \
	-cp %{_javadir}/guava.jar:%{_javadir}/failureaccess.jar \
	-d ann-classes @ann-sources.list
jar cf auto-value-annotations.jar -C ann-classes .
jar tf auto-value-annotations.jar | grep -E '\.(java|jar|so|node|wasm)$' && exit 1 || true

find "$JAVA/processor" -name '*.java' ! -name 'module-info.java' > proc-sources.list
find "$JAVA/extension/memoized/processor" -name '*.java' >> proc-sources.list
find "$JAVA/extension/serializable/processor" -name '*.java' >> proc-sources.list
find "$JAVA/extension/serializable/serializer" -name '*.java' >> proc-sources.list
find "$JAVA/extension/toprettystring/processor" -name '*.java' >> proc-sources.list
test "$(wc -l < proc-sources.list)" -eq 68
mkdir -p proc-classes
javac --release 11 -encoding UTF-8 \
	-cp ann-classes:%{_javadir}/guava.jar:%{_javadir}/failureaccess.jar:%{_javadir}/javapoet.jar:%{_javadir}/auto-common.jar:%{_javadir}/escapevelocity.jar:%{_javadir}/incap.jar:%{_javadir}/auto-service-annotations.jar:%{_javadir}/error_prone_annotations.jar:%{_javadir}/asm.jar \
	-d proc-classes @proc-sources.list
find value/src/main/java -name '*.vm' > vm.list
test "$(wc -l < vm.list)" -eq 8
while IFS= read -r template; do
	rel=${template#value/src/main/java/}
	mkdir -p "proc-classes/$(dirname "$rel")"
	/bin/cp -f "$template" "proc-classes/$rel"
done < vm.list
mkdir -p proc-classes/META-INF/services
cat > proc-classes/META-INF/services/javax.annotation.processing.Processor << 'EOF'
com.google.auto.value.processor.AutoAnnotationProcessor
com.google.auto.value.processor.AutoBuilderProcessor
com.google.auto.value.processor.AutoOneOfProcessor
com.google.auto.value.processor.AutoValueBuilderProcessor
com.google.auto.value.processor.AutoValueProcessor
com.google.auto.value.extension.memoized.processor.MemoizedValidator
com.google.auto.value.extension.toprettystring.processor.ToPrettyStringValidator
EOF
cat > proc-classes/META-INF/services/com.google.auto.value.extension.AutoValueExtension << 'EOF'
com.google.auto.value.extension.memoized.processor.MemoizeExtension
com.google.auto.value.extension.serializable.processor.SerializableAutoValueExtension
com.google.auto.value.extension.toprettystring.processor.ToPrettyStringExtension
EOF
cat > proc-classes/META-INF/services/com.google.auto.value.extension.serializable.serializer.interfaces.SerializerExtension << 'EOF'
com.google.auto.value.extension.serializable.serializer.impl.ImmutableListSerializerExtension
com.google.auto.value.extension.serializable.serializer.impl.ImmutableMapSerializerExtension
com.google.auto.value.extension.serializable.serializer.impl.OptionalSerializerExtension
EOF
jar cf auto-value.jar -C proc-classes .
jar tf auto-value.jar | grep -E '\.(java|jar|so|node|wasm)$' && exit 1 || true
jar tf auto-value.jar | grep -F -q 'com/google/auto/value/processor/autovalue.vm'
javap -verbose -cp auto-value.jar com.google.auto.value.processor.AutoValueProcessor | grep -F 'major version: 55'

cat > auto-value-annotations.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.google.auto.value</groupId>
  <artifactId>auto-value-annotations</artifactId>
  <version>1.11.1</version>
  <name>AutoValue Annotations</name>
  <description>Annotations for AutoValue immutable types</description>
  <licenses>
    <license>
      <name>Apache-2.0</name>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>com.google.guava</groupId>
      <artifactId>guava</artifactId>
      <version>33.6.0-jre</version>
    </dependency>
  </dependencies>
</project>
EOF

cat > auto-value.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.google.auto.value</groupId>
  <artifactId>auto-value</artifactId>
  <version>1.11.1</version>
  <name>AutoValue Processor</name>
  <description>Annotation processor that generates AutoValue classes</description>
  <licenses>
    <license>
      <name>Apache-2.0</name>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>com.google.auto.value</groupId>
      <artifactId>auto-value-annotations</artifactId>
      <version>1.11.1</version>
    </dependency>
    <dependency>
      <groupId>com.google.auto</groupId>
      <artifactId>auto-common</artifactId>
      <version>1.2.2</version>
    </dependency>
    <dependency>
      <groupId>com.google.escapevelocity</groupId>
      <artifactId>escapevelocity</artifactId>
      <version>1.1</version>
    </dependency>
    <dependency>
      <groupId>com.google.guava</groupId>
      <artifactId>guava</artifactId>
      <version>33.6.0-jre</version>
    </dependency>
    <dependency>
      <groupId>com.squareup</groupId>
      <artifactId>javapoet</artifactId>
      <version>1.13.0</version>
    </dependency>
    <dependency>
      <groupId>org.ow2.asm</groupId>
      <artifactId>asm</artifactId>
      <version>9.11.1</version>
    </dependency>
    <dependency>
      <groupId>com.google.auto.service</groupId>
      <artifactId>auto-service-annotations</artifactId>
      <version>1.1.1</version>
      <optional>true</optional>
    </dependency>
    <dependency>
      <groupId>net.ltgt.gradle.incap</groupId>
      <artifactId>incap</artifactId>
      <version>1.0.0</version>
      <optional>true</optional>
    </dependency>
    <dependency>
      <groupId>com.google.errorprone</groupId>
      <artifactId>error_prone_annotations</artifactId>
      <version>2.52.0</version>
      <optional>true</optional>
    </dependency>
  </dependencies>
</project>
EOF

%install
sysjar install --buildroot %{buildroot} \
	--artifact auto-value-annotations.pom:auto-value-annotations.jar \
	--file-name auto-value-annotations \
	--filelist .mfiles-ann
sysjar install --buildroot %{buildroot} \
	--artifact auto-value.pom:auto-value.jar \
	--file-name auto-value \
	--filelist .mfiles-proc
awk '!seen[$0]++' .mfiles-ann .mfiles-proc > .mfiles

%check
mkdir -p check
cat > check/Animal.java << 'END'
import com.google.auto.value.AutoValue;
@AutoValue
abstract class Animal {
	abstract String name();
	static Animal create(String name) {
		return new AutoValue_Animal(name);
	}
}
END
cat > check/Smoke.java << 'END'
public class Smoke {
	public static void main(String[] args) {
		Animal animal = Animal.create("gradle");
		if (!"gradle".equals(animal.name())) {
			throw new RuntimeException(animal.name());
		}
		System.out.println("autovalue_ok " + animal.name() + " " + animal.getClass().getSimpleName());
	}
}
END
ANN=%{buildroot}%{_javadir}/auto-value-annotations.jar
PROC=%{buildroot}%{_javadir}/auto-value.jar
test -f "$ANN"
test -f "$PROC"
CP="$ANN:$PROC:%{_javadir}/auto-common.jar:%{_javadir}/escapevelocity.jar:%{_javadir}/guava.jar:%{_javadir}/failureaccess.jar:%{_javadir}/javapoet.jar:%{_javadir}/asm.jar:%{_javadir}/incap.jar:%{_javadir}/auto-service-annotations.jar:%{_javadir}/error_prone_annotations.jar"
javac --release 11 -encoding UTF-8 -proc:full -cp "$CP" -d check check/Animal.java check/Smoke.java
test -f check/AutoValue_Animal.class
java -cp "check:$ANN" Smoke > check/out.txt
cat check/out.txt
grep -F -q 'autovalue_ok gradle AutoValue_Animal' check/out.txt

%files -f .mfiles
%doc LICENSE
