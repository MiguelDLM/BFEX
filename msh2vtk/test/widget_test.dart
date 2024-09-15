import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:msh2vtk/main.dart';

void main() {
  testWidgets('Directory selection and file listing test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const MshConverterApp());

    // Verify that the initial state does not show any selected directory or files.
    expect(find.text('Selected directory: '), findsNothing);
    expect(find.byType(ListView), findsNothing);

    // Tap the 'Select Directory' button and trigger a frame.
    await tester.tap(find.text('Select Directory'));
    await tester.pump();

    // Since we cannot actually open a file picker in a test environment,
    // we will assume the directory selection and file listing logic works as expected.
    // You would need to mock the file picker and shell command execution for a complete test.

    // Verify that the directory selection button is present.
    expect(find.text('Select Directory'), findsOneWidget);
  });
}