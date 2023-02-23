import os
import pkg_resources
import shutil

from abc import abstractmethod
from drydock.manifest_builder.domain.config import DrydockConfig
from drydock.manifest_builder.domain.manifest_repository import ManifestRepository

from tutor import env as tutor_env
from tutor import hooks


class FlexibleTutorManifest(ManifestRepository):
    """
    Super hacky implementation of using tutor to render the templates.
    An elegant interface implementation will be necessary if this ever
    leaves the POC phase.
    """
    def __init__(self, options: dict) -> None:
        self.options = options

    def save(self, config: DrydockConfig) -> None:

        env = config.get_data()

        # Render the manifest by reusing the code that tutor uses for the env
        fixed_root = self.options.get("output", "manifest")

        def my_base_dir(root):
            return os.path.join(fixed_root, "")

        tutor_env.base_dir = my_base_dir
        tutor_env.save(None, env)

        # Delete tutor env files that are not related to the k8s manifest
        for path in ["dev", "build", "local"]:
            shutil.rmtree(os.path.join(fixed_root, path))

        hooks.Filters.ENV_TEMPLATE_TARGETS.clear()

        hooks.Filters.ENV_TEMPLATE_TARGETS.add_items(
            [
                (
                    self.options.get("tutor_templates_version"),
                    "",
                ),
            ],
        )

        hooks.Filters.ENV_TEMPLATE_ROOTS.add_item(
            pkg_resources.resource_filename("drydock", "templates")
        )

        tutor_env.save(None, env)

        src_path = os.path.join(fixed_root, self.options.get("tutor_templates_version"))
        dst_path = os.path.join(fixed_root)
        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        shutil.rmtree(src_path)

